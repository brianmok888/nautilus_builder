/**
 * Feed client — supports mock, snapshot API, and SSE modes.
 * Default: mock (safe, no backend required).
 *
 * No browser secrets. No Redis URL. No exchange API key.
 */
import type { TradeHudEvent } from "./types";
import { MockFeed } from "./mock-feed";

export type FeedMode = "mock" | "snapshot" | "sse";

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
      const poll = async () => {
        try {
          const res = await fetch(`${base}/api/tradehud/snapshot?symbol=${encodeURIComponent(symbol)}`);
          if (!res.ok) throw new Error(`HTTP ${res.status}`);
          const data = await res.json();
          dispatch({ type: "SET_BACKEND", payload: true });
          dispatch({ type: "SNAPSHOT", payload: data });
        } catch {
          dispatch({ type: "SET_BACKEND", payload: false });
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

// ─── SSE feed controller ──────────────────────────────────────────────────────

function createSseFeed(symbol: string): FeedController {
  let es: EventSource | null = null;
  const base = getApiBase();

  return {
    mode: "sse",
    start(dispatch) {
      try {
        es = new EventSource(`${base}/api/tradehud/stream?symbol=${encodeURIComponent(symbol)}`);
        es.onopen = () => dispatch({ type: "SET_BACKEND", payload: true });
        es.onerror = () => dispatch({ type: "SET_BACKEND", payload: false });
        es.onmessage = (ev) => {
          try {
            const event = JSON.parse(ev.data) as TradeHudEvent;
            dispatch(event);
          } catch {
            // ignore malformed
          }
        };
      } catch {
        dispatch({ type: "SET_BACKEND", payload: false });
      }
    },
    stop() {
      if (es) es.close();
    },
  };
}
