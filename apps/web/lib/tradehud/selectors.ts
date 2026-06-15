/**
 * Selectors — extract prepared, display-ready slices from TradeHudState.
 * Components receive already-computed data, no heavy work in render.
 */
import type {
  TradeHudState,
  BookLevel,
  MarketTrade,
  RuntimeHealth,
  LaneHealth,
} from "./types";

export function selectOrderBookTopN(state: TradeHudState, n: number = 12): {
  asks: BookLevel[];
  bids: BookLevel[];
  spread: number;
  spreadBps: number;
  microprice: number;
  top5Imbalance: number;
  checksum: string | null;
} {
  const l2 = state.bookL2;
  if (!l2) {
    return { asks: [], bids: [], spread: 0, spreadBps: 0, microprice: 0, top5Imbalance: 0.5, checksum: null };
  }
  return {
    asks: l2.asks.slice(0, n),
    bids: l2.bids.slice(0, n),
    spread: l2.spread,
    spreadBps: l2.spread_bps,
    microprice: l2.microprice,
    top5Imbalance: l2.top5_imbalance,
    checksum: l2.checksum,
  };
}

export function selectRecentTrades(state: TradeHudState, n: number = 50): MarketTrade[] {
  return state.trades.slice(0, n);
}

export function selectLanes(state: TradeHudState): LaneHealth[] {
  const h = state.runtimeHealth;
  if (!h) return [];
  return [
    h.run_main_strategy_signal,
    h.run_gate_engine,
    h.run_execution_lane,
    h.ai_lane_advisory,
    h.data_health,
  ];
}

export function selectPriceRange(state: TradeHudState): { min: number; max: number } {
  const price = state.bookTop?.mid_price ?? 0;
  if (!price) return { min: 0, max: 1 };
  const offset = price * 0.01;
  return { min: price - offset, max: price + offset };
}
