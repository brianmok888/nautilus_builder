/**
 * Feed client — supports mock, snapshot API, and SSE modes.
 * Default: mock (safe, no backend required).
 *
 * SSE mode features:
 * - Auto-fallback to mock feed if SSE connection fails
 * - Exponential backoff reconnection (3 attempts)
 * - Connection status tracking via SET_FEED_STATUS events
 * - Clean teardown on component unmount
 *
 * No browser secrets. No Redis URL. No exchange API key.
 */
import type { TradeHudEvent } from "./types";
import { MockFeed } from "./mock-feed";

export type FeedMode = "mock" | "snapshot" | "sse";
export type FeedStatus = "connecting" | "live" | "reconnecting" | "fallback" | "mock";

function getEnvMode(): FeedMode {
  const mode = process.env.NEXT_PUBLIC_TRADEHUD_FEED_MODE;
  if (mode === "snapshot" || mode === "sse") return mode;
  return "mock"; // safe default
}

function getApiBase(): string {
  return process.env.NEXT_PUBLIC_BUILDER_API_BASE ?? "http://127.0.0.1:8000";
}

export interface FeedController {
  start: (dispatch: (event: TradeHudEvent) => void) => void;
  stop: () => void;
  mode: FeedMode;
}

export function createFeed(symbol: string = "BTCUSDT-PERP"): FeedController {
  const mode = getEnvMode();

  if (mode === "snapshot") {
    return createSnapshotFeed(symbol);
  }
  if (mode === "sse") {
    return createSseFeed(symbol);
  }
  return createMockFeed(symbol);
}

// ─── Mock feed controller ─────────────────────────────────────────────────────

function createMockFeed(symbol: string): FeedController {
  let timer: ReturnType<typeof setInterval> | null = null;
  let gateCycle = 0;
  const feed = new MockFeed(symbol);

  return {
    mode: "mock",
    start(dispatch) {
      // Emit initial snapshot
      dispatch({ type: "SET_BACKEND", payload: false });
      dispatch({ type: "SET_FEED_STATUS", payload: { status: "mock", mode: "mock" } });
      dispatch({
        type: "SNAPSHOT",
        payload: {
          bookTop: feed.getBookTop(),
          bookL2: feed.getBookL2(),
          positions: feed.getPositions(),
          openOrders: feed.getOpenOrders(),
          account: feed.getAccount(),
          assets: feed.getAssets(),
          quantLevels: feed.getQuantLevels(),
          runtimeHealth: feed.getRuntimeHealth(),
          tickToTrade: feed.getTickToTrade(),
          feedMode: "mock" as const,
        },
      });
      dispatch({ type: "SIGNAL_PREVIEW", payload: feed.getSignalPreview() });
      dispatch({ type: "GATE_DECISION", payload: feed.getGateDecision(gateCycle++) });
      dispatch({ type: "GATE_DECISION", payload: feed.getGateDecision(gateCycle++) });
      dispatch({ type: "GATE_DECISION", payload: feed.getGateDecision(gateCycle++) });
      dispatch({ type: "EXECUTION_REPORT", payload: feed.getExecutionReport() });
      feed.getTrades().forEach((t) => dispatch({ type: "TRADE", payload: t }));

      // Periodic updates
      timer = setInterval(() => {
        feed.tick();
        dispatch({ type: "BOOK_TOP", payload: feed.getBookTop() });
        dispatch({ type: "BOOK_L2", payload: feed.getBookL2() });
        dispatch({ type: "ACCOUNT", payload: feed.getAccount() });
        dispatch({ type: "POSITIONS", payload: feed.getPositions() });
        dispatch({ type: "OPEN_ORDERS", payload: feed.getOpenOrders() });
        dispatch({ type: "RUNTIME_HEALTH", payload: feed.getRuntimeHealth() });
        dispatch({ type: "TICK_TO_TRADE", payload: feed.getTickToTrade() });
        dispatch({ type: "QUANT_LEVELS", payload: feed.getQuantLevels() });

        // Emit recent trade
        const trades = feed.getTrades().slice(0, 3);
        trades.forEach((t) => dispatch({ type: "TRADE", payload: t }));

        // Periodically emit new evidence
        if (gateCycle % 10 === 0) {
          dispatch({ type: "SIGNAL_PREVIEW", payload: feed.getSignalPreview() });
          const gate = feed.getGateDecision(gateCycle);
          dispatch({ type: "GATE_DECISION", payload: gate });
          if (gate.decision === "APPROVED") {
            const ta = feed.getTradeActionEvidence(gate.gate_decision_hash);
            dispatch({ type: "TRADE_ACTION", payload: ta });
            dispatch({ type: "EXECUTION_REPORT", payload: feed.getExecutionReport() });
          }
        }
        gateCycle++;
      }, 1500);
    },
    stop() {
      if (timer) clearInterval(timer);
    },
  };
}

// ─── Snapshot API feed controller ─────────────────────────────────────────────

function createSnapshotFeed(symbol: string): FeedController {
  let timer: ReturnType<typeof setInterval> | null = null;
  const base = getApiBase();

  return {
    mode: "snapshot",
    start(dispatch) {
      dispatch({ type: "SET_FEED_STATUS", payload: { status: "connecting", mode: "snapshot" } });
      const poll = async () => {
        try {
          const res = await fetch(`${base}/api/tradehud/snapshot?symbol=${encodeURIComponent(symbol)}`);
          if (!res.ok) throw new Error(`HTTP ${res.status}`);
          const data = await res.json();
          dispatch({ type: "SET_BACKEND", payload: true });
          dispatch({ type: "SET_FEED_STATUS", payload: { status: "live", mode: "snapshot" } });
          dispatch({ type: "SNAPSHOT", payload: data });
        } catch {
          dispatch({ type: "SET_BACKEND", payload: false });
          dispatch({ type: "SET_FEED_STATUS", payload: { status: "fallback", mode: "snapshot" } });
        }
      };
      poll();
      timer = setInterval(poll, 2000);
    },
    stop() {
      if (timer) clearInterval(timer);
    },
  };
}

// ─── SSE feed controller with auto-fallback ───────────────────────────────────

const SSE_RECONNECT_DELAYS = [1000, 3000, 5000]; // exponential backoff

function createSseFeed(symbol: string): FeedController {
  let es: EventSource | null = null;
  let mockFallback: FeedController | null = null;
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  let reconnectAttempts = 0;
  let stopped = false;
  const base = getApiBase();

  function connect(dispatch: (event: TradeHudEvent) => void) {
    if (stopped) return;

    dispatch({ type: "SET_FEED_STATUS", payload: { status: reconnectAttempts > 0 ? "reconnecting" : "connecting", mode: "sse" } });

    try {
      es = new EventSource(`${base}/api/tradehud/stream?symbol=${encodeURIComponent(symbol)}`);
    } catch {
      attemptFallback(dispatch);
      return;
    }

    es.onopen = () => {
      reconnectAttempts = 0;
      dispatch({ type: "SET_BACKEND", payload: true });
      dispatch({ type: "SET_FEED_STATUS", payload: { status: "live", mode: "sse" } });
      // Stop mock fallback if it was running
      if (mockFallback) {
        mockFallback.stop();
        mockFallback = null;
      }
    };

    es.onerror = () => {
      es?.close();
      es = null;
      dispatch({ type: "SET_BACKEND", payload: false });

      if (reconnectAttempts < SSE_RECONNECT_DELAYS.length) {
        dispatch({ type: "SET_FEED_STATUS", payload: { status: "reconnecting", mode: "sse" } });
        const delay = SSE_RECONNECT_DELAYS[reconnectAttempts++];
        reconnectTimer = setTimeout(() => connect(dispatch), delay);
      } else {
        // All reconnection attempts exhausted — fall back to mock
        attemptFallback(dispatch);
      }
    };

    es.onmessage = (ev) => {
      try {
        const event = JSON.parse(ev.data) as TradeHudEvent;
        dispatch(event);
      } catch {
        // ignore malformed
      }
    };
  }

  function attemptFallback(dispatch: (event: TradeHudEvent) => void) {
    if (mockFallback) return;
    dispatch({ type: "SET_FEED_STATUS", payload: { status: "fallback", mode: "sse" } });
    mockFallback = createMockFeed(symbol);
    mockFallback.start(dispatch);
  }

  return {
    mode: "sse",
    start(dispatch) {
      stopped = false;
      connect(dispatch);
    },
    stop() {
      stopped = true;
      if (es) { es.close(); es = null; }
      if (reconnectTimer) { clearTimeout(reconnectTimer); reconnectTimer = null; }
      if (mockFallback) { mockFallback.stop(); mockFallback = null; }
    },
  };
}
