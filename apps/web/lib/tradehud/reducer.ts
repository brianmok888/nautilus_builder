/**
 * Central TradeHUD state reducer.
 * Accepts typed events and updates bounded TradeHudState.
 * Arrays are capped to prevent unbounded growth.
 */
import type { TradeHudState, TradeHudEvent } from "./types";
import { MAX_TRADES, MAX_ORDER_EVENTS, MAX_FILLS, MAX_BARS, MAX_LIQUIDATIONS } from "./types";

export function createInitialState(): TradeHudState {
  return {
    selectedVenue: "BINANCE-FUTURES",
    selectedSymbol: "BTCUSDT-PERP",
    selectedAccount: "acc_paper_001",
    mode: "paper",

    bookTop: null,
    bookL2: null,
    trades: [],
    bars: [],
    liquidations: [],

    latestSignalPreview: null,
    latestGateDecision: null,
    latestTradeAction: null,
    latestExecutionReport: null,

    positions: [],
    openOrders: [],
    orderHistory: [],
    tradeHistory: [],
    account: null,
    assets: [],

    quantLevels: null,
    tickToTrade: null,
    runtimeHealth: null,

    backendAvailable: false,
    feedMode: "mock",
  };
}

function pushBounded<T>(arr: T[], item: T, limit: number): T[] {
  const next = [...arr, item];
  return next.length > limit ? next.slice(next.length - limit) : next;
}

export function reducer(state: TradeHudState, event: TradeHudEvent): TradeHudState {
  switch (event.type) {
    case "BOOK_TOP":
      return { ...state, bookTop: event.payload };

    case "BOOK_L2":
      return { ...state, bookL2: event.payload };

    case "TRADE":
      return { ...state, trades: pushBounded(state.trades, event.payload, MAX_TRADES) };

    case "BAR":
      return { ...state, bars: pushBounded(state.bars, event.payload, MAX_BARS) };

    case "LIQUIDATION":
      return { ...state, liquidations: pushBounded(state.liquidations, event.payload, MAX_LIQUIDATIONS) };

    case "SIGNAL_PREVIEW":
      return { ...state, latestSignalPreview: event.payload };

    case "GATE_DECISION":
      return { ...state, latestGateDecision: event.payload };

    case "TRADE_ACTION":
      return { ...state, latestTradeAction: event.payload };

    case "EXECUTION_REPORT":
      return { ...state, latestExecutionReport: event.payload };

    case "POSITIONS":
      return { ...state, positions: event.payload };

    case "OPEN_ORDERS":
      return { ...state, openOrders: event.payload };

    case "ORDER_EVENT":
      return { ...state, orderHistory: pushBounded(state.orderHistory, event.payload, MAX_ORDER_EVENTS) };

    case "FILL_EVENT":
      return { ...state, tradeHistory: pushBounded(state.tradeHistory, event.payload, MAX_FILLS) };

    case "ACCOUNT":
      return { ...state, account: event.payload };

    case "ASSETS":
      return { ...state, assets: event.payload };

    case "QUANT_LEVELS":
      return { ...state, quantLevels: event.payload };

    case "TICK_TO_TRADE":
      return { ...state, tickToTrade: event.payload };

    case "RUNTIME_HEALTH":
      return { ...state, runtimeHealth: event.payload };

    case "SNAPSHOT":
      return { ...state, ...event.payload };

    case "SET_MODE":
      return { ...state, mode: event.payload };

    case "SET_BACKEND":
      return { ...state, backendAvailable: event.payload };

    default:
      return state;
  }
}
