/**
 * Feed client — supports mock, snapshot API, and SSE modes.
 * Default: mock (safe, no backend required).
 *
 * SSE mode features:
 * - Named event listeners (snapshot, tradehud_event, ping, stream_health)
 * - Redis-aware feed status tracking (redis_live, redis_degraded, stream_stale, etc.)
 * - Auto-fallback to mock feed if SSE connection fails after bounded retries
 * - Bounded exponential backoff with jitter (500ms initial, 15s max)
 * - Connection status tracking via SET_FEED_STATUS events
 * - Clean teardown on component unmount — closes EventSource, clears timers
 *
 * No browser secrets. No Redis URL. No exchange API key.
 */
import type { TradeHudEvent } from "./types";
import { MockFeed } from "./mock-feed";

export type FeedMode = "mock" | "snapshot" | "sse";
export type FeedStatus =
  | "connecting"
  | "live"
  | "reconnecting"
  | "fallback"
  | "mock"
  | "redis_live"
  | "redis_degraded"
  | "redis_disconnected"
  | "stream_stale"
  | "stream_missing";

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

        const trades = feed.getTrades().slice(0, 3);
        trades.forEach((t) => dispatch({ type: "TRADE", payload: t }));

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

// ─── SSE feed controller with bounded backoff + Redis awareness ──────────────────

const SSE_MAX_RETRIES = 5;
const SSE_BACKOFF_INITIAL = 500;
const SSE_BACKOFF_MAX = 15000;

function backoffDelay(attempt: number): number {
  const base = Math.min(SSE_BACKOFF_INITIAL * 2 ** attempt, SSE_BACKOFF_MAX);
  const jitter = base * 0.1 * (Math.random() * 2 - 1);
  return Math.round(base + jitter);
}

/** Dispatch a single SSE tradehud_event payload field as individual reducer events. */
function dispatchSseEvent(data: any, dispatch: (event: TradeHudEvent) => void) {
  if (data.book_top) dispatch({ type: "BOOK_TOP", payload: data.book_top });
  if (data.book_l2) dispatch({ type: "BOOK_L2", payload: data.book_l2 });
  if (data.account) dispatch({ type: "ACCOUNT", payload: data.account });
  if (data.positions) dispatch({ type: "POSITIONS", payload: data.positions });
  if (data.quant_levels) dispatch({ type: "QUANT_LEVELS", payload: data.quant_levels });
  if (data.runtime_health) dispatch({ type: "RUNTIME_HEALTH", payload: data.runtime_health });
  if (data.signal_preview) dispatch({ type: "SIGNAL_PREVIEW", payload: data.signal_preview });
  if (data.gate_decision) dispatch({ type: "GATE_DECISION", payload: data.gate_decision });
}

/** Dispatch Redis trade events. */
function dispatchRedisTrades(data: any, dispatch: (event: TradeHudEvent) => void) {
  const trades = data.trades;
  if (Array.isArray(trades)) {
    trades.forEach((t: any) => dispatch({ type: "TRADE", payload: t }));
  }
}

/** Derive feed status from SSE event provenance and stream health. */
function deriveFeedStatus(data: any): string {
  const provenance = data.provenance;
  const sourceStatus = data.source_status;
  if (provenance === "redis" && sourceStatus === "live") return "redis_live";
  if (provenance === "redis") return "redis_degraded";
  return "live";
}

function createSseFeed(symbol: string): FeedController {
  let es: EventSource | null = null;
  let mockFallback: FeedController | null = null;
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  let reconnectAttempts = 0;
  let stopped = false;
  const base = getApiBase();

  function connect(dispatch: (event: TradeHudEvent) => void) {
    if (stopped) return;

    dispatch({
      type: "SET_FEED_STATUS",
      payload: { status: reconnectAttempts > 0 ? "reconnecting" : "connecting", mode: "sse" },
    });

    try {
      es = new EventSource(`${base}/api/tradehud/stream?symbol=${encodeURIComponent(symbol)}`);
    } catch {
      attemptFallback(dispatch);
      return;
    }

    es.addEventListener("open", () => {
      reconnectAttempts = 0;
      dispatch({ type: "SET_BACKEND", payload: true });
      dispatch({ type: "SET_FEED_STATUS", payload: { status: "live", mode: "sse" } });
      if (mockFallback) {
        mockFallback.stop();
        mockFallback = null;
      }
    });

    es.addEventListener("error", () => {
      es?.close();
      es = null;
      dispatch({ type: "SET_BACKEND", payload: false });
      dispatch({ type: "SET_FEED_STATUS", payload: { status: "redis_disconnected", mode: "sse" } });

      if (reconnectAttempts < SSE_MAX_RETRIES) {
        const delay = backoffDelay(reconnectAttempts++);
        reconnectTimer = setTimeout(() => connect(dispatch), delay);
      } else {
        attemptFallback(dispatch);
      }
    });

    // Named event: snapshot
    es.addEventListener("snapshot", (ev: MessageEvent) => {
      try {
        const data = JSON.parse(ev.data);
        dispatch({ type: "SET_BACKEND", payload: true });
        dispatchSseEvent(data, dispatch);
        dispatchRedisTrades(data, dispatch);
        const status = deriveFeedStatus(data);
        dispatch({ type: "SET_FEED_STATUS", payload: { status, mode: "sse" } });
      } catch {
        // ignore malformed
      }
    });

    // Named event: tradehud_event
    es.addEventListener("tradehud_event", (ev: MessageEvent) => {
      try {
        const data = JSON.parse(ev.data);
        dispatchSseEvent(data, dispatch);
        dispatchRedisTrades(data, dispatch);
        const status = deriveFeedStatus(data);
        dispatch({ type: "SET_FEED_STATUS", payload: { status, mode: "sse" } });
      } catch {
        // ignore malformed
      }
    });

    // Named event: stream_health (Redis mode only)
    es.addEventListener("stream_health", (ev: MessageEvent) => {
      try {
        const data = JSON.parse(ev.data);
        const health = data.stream_health;
        if (!health) return;
        // Derive aggregate status from stream health
        if (health.streams_missing && health.streams_missing.length > 0) {
          dispatch({ type: "SET_FEED_STATUS", payload: { status: "stream_missing", mode: "sse" } });
        } else if (health.streams_stale && health.streams_stale.length > 0) {
          dispatch({ type: "SET_FEED_STATUS", payload: { status: "stream_stale", mode: "sse" } });
        } else if (data.redis_connected) {
          dispatch({ type: "SET_FEED_STATUS", payload: { status: "redis_live", mode: "sse" } });
        } else {
          dispatch({ type: "SET_FEED_STATUS", payload: { status: "redis_degraded", mode: "sse" } });
        }
      } catch {
        // ignore malformed
      }
    });

    // Named event: ping
    es.addEventListener("ping", () => {
      dispatch({ type: "SET_FEED_STATUS", payload: { status: "live", mode: "sse" } });
    });
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
