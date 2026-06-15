import { describe, it, expect } from "vitest";
import { createInitialState, reducer } from "./reducer";
import type { TradeHudEvent, MarketTrade, StrategySignalPreview, GateDecision, ExecutionReport, AccountSnapshot } from "./types";

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

describe("TradeHUD reducer", () => {
  it("initializes with safe defaults (mock mode)", () => {
    const state = createInitialState();
    expect(state.selectedSymbol).toBe("BTCUSDT-PERP");
    expect(state.backendAvailable).toBe(false);
    expect(state.trades).toEqual([]);
    expect(state.positions).toEqual([]);
  });

  it("handles TRADE events and caps trades at MAX_TRADES", () => {
    let state = createInitialState();

    for (let i = 0; i < 600; i++) {
      const trade: MarketTrade = {
        trade_id: `t${i}`,
        symbol: "BTCUSDT-PERP",
        price: 105000,
        qty: 0.01,
        notional: 1050,
        side: i % 2 === 0 ? "buy" : "sell",
        aggressor: "buy",
        source: "mock",
        is_large_trade: false,
        is_sweep: false,
        is_liquidation: false,
        liq_side: null,
        ts_event_ns: NOW_NS + i,
        ...freshMeta(NOW_NS + i),
      };
      state = reducer(state, { type: "TRADE", payload: trade });
    }

    expect(state.trades.length).toBeLessThanOrEqual(500);
  });

  it("handles SIGNAL_PREVIEW events", () => {
    let state = createInitialState();
    const signal: StrategySignalPreview = {
      signal_id: "sig_1",
      symbol: "BTCUSDT-PERP",
      feature_hash: "abc",
      context_hash: "def",
      policy_hash: "ghi",
      graph_trace_hash: "jkl",
      confidence_score: 0.72,
      direction: "long",
      target_hint: 106000,
      invalidation_hint: 104500,
      size_hint: 0.5,
      preview_note: "Preview only — NOT EXECUTABLE",
      ts_event_ns: NOW_NS,
      ...freshMeta(NOW_NS),
    };
    state = reducer(state, { type: "SIGNAL_PREVIEW", payload: signal });
    expect(state.latestSignalPreview).not.toBeNull();
    expect(state.latestSignalPreview?.direction).toBe("long");
  });

  it("handles GATE_DECISION events (approved/rejected/hold)", () => {
    let state = createInitialState();
    for (const decision of ["APPROVED", "REJECTED", "HOLD"] as const) {
      const gate: GateDecision = {
        decision_id: `gate_${decision}`,
        decision,
        first_blocking_gate: decision === "APPROVED" ? null : "risk_size_gate",
        reason_code: decision === "APPROVED" ? "all_passed" : "blocked",
        confidence_delta: 0.05,
        size_modifier: 0.8,
        target_hint: 105500,
        invalidation_hint: 104500,
        gate_decision_hash: `gd_${decision}`,
        source_signal_hash: "sig_hash",
        ts_event_ns: NOW_NS,
        ...freshMeta(NOW_NS),
      };
      state = reducer(state, { type: "GATE_DECISION", payload: gate });
    }
    expect(state.latestGateDecision?.decision).toBe("HOLD");
  });

  it("handles EXECUTION_REPORT events", () => {
    let state = createInitialState();
    const report: ExecutionReport = {
      report_id: "exec_1",
      status: "FILLED",
      exchange_order_id: "BIN-123",
      client_order_id: "CO-1",
      trade_action_hash: "ta_hash",
      symbol: "BTCUSDT-PERP",
      side: "buy",
      filled_qty: 0.1,
      avg_fill_price: 105000,
      submit_ts_ns: NOW_NS - 1000,
      ack_ts_ns: NOW_NS - 500,
      fill_ts_ns: NOW_NS,
      submit_to_ack_us: 500,
      ack_to_fill_us: 500,
      rejection_reason: null,
      ts_event_ns: NOW_NS,
      ...freshMeta(NOW_NS),
    };
    state = reducer(state, { type: "EXECUTION_REPORT", payload: report });
    expect(state.latestExecutionReport?.status).toBe("FILLED");
    expect(state.latestExecutionReport?.filled_qty).toBe(0.1);
  });

  it("handles ACCOUNT events", () => {
    let state = createInitialState();
    const account: AccountSnapshot = {
      account_id: "acc_1",
      venue: "BINANCE-FUTURES",
      balance: 250000,
      equity: 251000,
      available_margin: 200000,
      margin_used: 51000,
      unrealized_pnl: 1000,
      realized_pnl: 5000,
      currency: "USDT",
      ts_event_ns: NOW_NS,
      ...freshMeta(NOW_NS),
    };
    state = reducer(state, { type: "ACCOUNT", payload: account });
    expect(state.account?.equity).toBe(251000);
  });

  it("handles SET_BACKEND events", () => {
    let state = createInitialState();
    state = reducer(state, { type: "SET_BACKEND", payload: true });
    expect(state.backendAvailable).toBe(true);
  });

  it("missing source is NOT treated as true_zero", () => {
    const state = createInitialState();
    // Initial state has null book — it's missing, not true_zero
    expect(state.bookL2).toBeNull();
    // When we build freshness for null data, missing=true, true_zero=false
    // Verified in freshness.test.ts
  });
});
