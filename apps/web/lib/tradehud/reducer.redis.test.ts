import { describe, it, expect } from "vitest";
import { createInitialState, reducer } from "./reducer";
import type { TradeHudState, MarketTrade } from "./types";

const NOW_NS = Date.now() * 1_000_000;

function freshMeta(ts: number) {
  return {
    source_available: true,
    last_update_ts_ns: ts,
    receive_ts_ns: ts,
    age_ms: 0,
    stale: false,
    missing: false,
    true_zero: false,
    provenance: "mock",
    source_status: "synthetic" as const,
  };
}

function tradeEvent(id: string, price: number): MarketTrade {
  return {
    trade_id: id,
    symbol: "BTCUSDT-PERP",
    price,
    qty: 0.01,
    notional: price * 0.01,
    side: "buy",
    aggressor: "buy",
    source: "redis",
    is_large_trade: false,
    is_sweep: false,
    is_liquidation: false,
    liq_side: null,
    ts_event_ns: NOW_NS,
    ...freshMeta(NOW_NS),
  };
}

describe("TradeHUD reducer — Redis feed status", () => {
  it("SET_FEED_STATUS updates feedStatus and feedMode", () => {
    let state = createInitialState();
    state = reducer(state, { type: "SET_FEED_STATUS", payload: { status: "redis_live", mode: "sse" } });
    expect(state.feedStatus).toBe("redis_live");
    expect(state.feedMode).toBe("sse");
  });

  it("SET_FEED_STATUS handles redis_degraded", () => {
    let state = createInitialState();
    state = reducer(state, { type: "SET_FEED_STATUS", payload: { status: "redis_degraded", mode: "sse" } });
    expect(state.feedStatus).toBe("redis_degraded");
  });

  it("SET_FEED_STATUS handles stream_stale", () => {
    let state = createInitialState();
    state = reducer(state, { type: "SET_FEED_STATUS", payload: { status: "stream_stale", mode: "sse" } });
    expect(state.feedStatus).toBe("stream_stale");
  });

  it("SET_FEED_STATUS handles stream_missing", () => {
    let state = createInitialState();
    state = reducer(state, { type: "SET_FEED_STATUS", payload: { status: "stream_missing", mode: "sse" } });
    expect(state.feedStatus).toBe("stream_missing");
  });

  it("SET_FEED_STATUS handles redis_disconnected", () => {
    let state = createInitialState();
    state = reducer(state, { type: "SET_FEED_STATUS", payload: { status: "redis_disconnected", mode: "sse" } });
    expect(state.feedStatus).toBe("redis_disconnected");
  });

  it("TRADE events from Redis are appended with source=redis", () => {
    let state = createInitialState();
    state = reducer(state, { type: "TRADE", payload: tradeEvent("t1", 67250) });
    state = reducer(state, { type: "TRADE", payload: tradeEvent("t2", 67260) });
    expect(state.trades.length).toBe(2);
    expect(state.trades[0].source).toBe("redis");
  });

  it("trades are still capped at MAX_TRADES in Redis mode", () => {
    let state = createInitialState();
    state = reducer(state, { type: "SET_FEED_STATUS", payload: { status: "redis_live", mode: "sse" } });
    for (let i = 0; i < 600; i++) {
      state = reducer(state, { type: "TRADE", payload: tradeEvent(`t${i}`, 67000 + i) });
    }
    expect(state.trades.length).toBeLessThanOrEqual(500);
  });

  it("falling back to mock clears Redis status", () => {
    let state = createInitialState();
    state = reducer(state, { type: "SET_FEED_STATUS", payload: { status: "redis_live", mode: "sse" } });
    state = reducer(state, { type: "SET_FEED_STATUS", payload: { status: "fallback", mode: "sse" } });
    expect(state.feedStatus).toBe("fallback");
  });
});
