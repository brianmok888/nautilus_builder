/**
 * TradeHUD TypeScript types — observational runtime monitoring.
 *
 * Browser displays runtime evidence only.
 * Browser has NO order authority.
 * Browser does NOT create TradeAction, submit_order, or hold credentials.
 */

// ─── Freshness / Source metadata ───────────────────────────────────────────────

export type SourceStatus =
  | "live"
  | "stale"
  | "missing"
  | "synthetic"
  | "true_zero"
  | "unavailable"
  | "unknown";

export interface SourceFreshnessMeta {
  source_available: boolean;
  last_update_ts_ns: number | null;
  receive_ts_ns: number | null;
  age_ms: number | null;
  stale: boolean;
  missing: boolean;
  true_zero: boolean;
  provenance: string;
  source_status: SourceStatus;
}

// ─── Market data ──────────────────────────────────────────────────────────────

export interface MarketBookTop extends SourceFreshnessMeta {
  symbol: string;
  bid_price: number;
  ask_price: number;
  bid_size: number;
  ask_size: number;
  mid_price: number;
  spread: number;
  spread_bps: number;
  microprice: number;
  ts_event_ns: number;
}

export interface BookLevel {
  price: number;
  size: number;
  total: number;
  age_ms: number;
  source: string;
}

export interface MarketBookL2 extends SourceFreshnessMeta {
  symbol: string;
  bids: BookLevel[];
  asks: BookLevel[];
  spread: number;
  spread_bps: number;
  microprice: number;
  top5_imbalance: number;
  checksum: string | null;
  ts_event_ns: number;
}

export interface MarketTrade extends SourceFreshnessMeta {
  trade_id: string;
  symbol: string;
  price: number;
  qty: number;
  notional: number;
  side: "buy" | "sell";
  aggressor: "buy" | "sell" | "unknown";
  source: string;
  is_large_trade: boolean;
  is_sweep: boolean;
  is_liquidation: boolean;
  liq_side: "long_liq" | "short_liq" | null;
  ts_event_ns: number;
}

export interface MarketBar extends SourceFreshnessMeta {
  symbol: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  ts_event_ns: number;
}

export interface LiquidationEvent extends SourceFreshnessMeta {
  symbol: string;
  price: number;
  qty: number;
  side: "buy" | "sell";
  liq_type: "long_liq" | "short_liq";
  ts_event_ns: number;
}

// ─── Heatmap cell ─────────────────────────────────────────────────────────────

export interface HeatmapCell {
  price_bucket: number;
  time_col: number;
  bid_intensity: number;
  ask_intensity: number;
}

// ─── ND-specific evidence types ────────────────────────────────────────────────

export interface StrategySignalPreview extends SourceFreshnessMeta {
  signal_id: string;
  symbol: string;
  feature_hash: string;
  context_hash: string;
  policy_hash: string;
  graph_trace_hash: string;
  confidence_score: number;
  direction: "long" | "short" | "flat";
  target_hint: number | null;
  invalidation_hint: number | null;
  size_hint: number | null;
  preview_note: string;
  ts_event_ns: number;
}

export type GateDecisionType = "APPROVED" | "HOLD" | "REJECTED";

export interface GateDecision extends SourceFreshnessMeta {
  decision_id: string;
  decision: GateDecisionType;
  first_blocking_gate: string | null;
  reason_code: string;
  confidence_delta: number;
  size_modifier: number;
  target_hint: number | null;
  invalidation_hint: number | null;
  gate_decision_hash: string;
  source_signal_hash: string;
  ts_event_ns: number;
}

export interface TradeActionEvidence extends SourceFreshnessMeta {
  action_id: string;
  action: string;
  side: "buy" | "sell";
  price: number;
  qty: number;
  trade_action_hash: string;
  source_gate_decision_hash: string;
  created_by: string;
  ts_event_ns: number;
}

export type ExecutionStatusType =
  | "SUBMITTED"
  | "ACKED"
  | "LIVE"
  | "PARTIAL_FILL"
  | "FILLED"
  | "CANCELED"
  | "REJECTED"
  | "EXPIRED";

export interface ExecutionReport extends SourceFreshnessMeta {
  report_id: string;
  status: ExecutionStatusType;
  exchange_order_id: string | null;
  client_order_id: string;
  trade_action_hash: string;
  symbol: string;
  side: "buy" | "sell";
  filled_qty: number;
  avg_fill_price: number | null;
  submit_ts_ns: number;
  ack_ts_ns: number | null;
  fill_ts_ns: number | null;
  submit_to_ack_us: number | null;
  ack_to_fill_us: number | null;
  rejection_reason: string | null;
  ts_event_ns: number;
}

// ─── Account / positions / orders ─────────────────────────────────────────────

export interface AccountSnapshot extends SourceFreshnessMeta {
  account_id: string;
  venue: string;
  balance: number;
  equity: number;
  available_margin: number;
  margin_used: number;
  unrealized_pnl: number;
  realized_pnl: number;
  currency: string;
  ts_event_ns: number;
}

export interface PositionSnapshot extends SourceFreshnessMeta {
  symbol: string;
  venue: string;
  side: "long" | "short" | "flat";
  qty: number;
  entry_price: number;
  mark_price: number;
  unrealized_pnl: number;
  realized_pnl: number;
  margin: number;
  ts_event_ns: number;
}

export interface OpenOrderSnapshot extends SourceFreshnessMeta {
  order_id: string;
  client_order_id: string;
  symbol: string;
  venue: string;
  side: "buy" | "sell";
  order_type: string;
  price: number;
  qty: number;
  filled_qty: number;
  status: ExecutionStatusType;
  ts_event_ns: number;
}

export interface AssetSnapshot extends SourceFreshnessMeta {
  asset: string;
  free: number;
  locked: number;
  usd_value: number;
}

// ─── Order / fill events ───────────────────────────────────────────────────────

export interface OrderEvent extends SourceFreshnessMeta {
  event_id: string;
  order_id: string;
  client_order_id: string;
  symbol: string;
  event_type: string;
  side: "buy" | "sell";
  price: number;
  qty: number;
  status: ExecutionStatusType;
  ts_event_ns: number;
}

export interface FillEvent extends SourceFreshnessMeta {
  fill_id: string;
  order_id: string;
  client_order_id: string;
  symbol: string;
  side: "buy" | "sell";
  price: number;
  qty: number;
  fee: number;
  ts_event_ns: number;
}

// ─── Quant / latency / health ─────────────────────────────────────────────────

export interface QuantLevel {
  label: string;
  price: number;
  kind: "support" | "resistance" | "pivot";
}

export interface QuantLevelsContext extends SourceFreshnessMeta {
  symbol: string;
  levels: QuantLevel[];
  ts_event_ns: number;
}

export interface TickToTradeTrace extends SourceFreshnessMeta {
  trace_id: string;
  tick_receive_ts_ns: number;
  signal_ts_ns: number;
  gate_ts_ns: number;
  execution_ts_ns: number;
  tick_to_signal_us: number;
  signal_to_gate_us: number;
  gate_to_execution_us: number;
  total_tick_to_trade_us: number;
  ts_event_ns: number;
}

export type LaneStatus = "healthy" | "stale" | "missing" | "degraded" | "unknown";

export interface LaneHealth {
  lane: string;
  status: LaneStatus;
  last_heartbeat_ts_ns: number | null;
  age_ms: number | null;
  stale: boolean;
  missing: boolean;
  reason_code: string | null;
}

export interface RuntimeHealth extends SourceFreshnessMeta {
  run_main_strategy_signal: LaneHealth;
  run_gate_engine: LaneHealth;
  run_execution_lane: LaneHealth;
  ai_lane_advisory: LaneHealth;
  data_health: LaneHealth;
  ts_event_ns: number;
}

// ─── Central state ─────────────────────────────────────────────────────────────

export interface TradeHudState {
  selectedVenue: string;
  selectedSymbol: string;
  selectedAccount: string;
  mode: "paper" | "live" | "backtest";

  bookTop: MarketBookTop | null;
  bookL2: MarketBookL2 | null;
  trades: MarketTrade[];
  bars: MarketBar[];
  liquidations: LiquidationEvent[];

  latestSignalPreview: StrategySignalPreview | null;
  latestGateDecision: GateDecision | null;
  latestTradeAction: TradeActionEvidence | null;
  latestExecutionReport: ExecutionReport | null;

  positions: PositionSnapshot[];
  openOrders: OpenOrderSnapshot[];
  orderHistory: OrderEvent[];
  tradeHistory: FillEvent[];
  account: AccountSnapshot | null;
  assets: AssetSnapshot[];

  quantLevels: QuantLevelsContext | null;
  tickToTrade: TickToTradeTrace | null;
  runtimeHealth: RuntimeHealth | null;

  backendAvailable: boolean;
  feedMode: "mock" | "snapshot" | "sse";
}

// ─── Reducer events ────────────────────────────────────────────────────────────

export type TradeHudEvent =
  | { type: "BOOK_TOP"; payload: MarketBookTop }
  | { type: "BOOK_L2"; payload: MarketBookL2 }
  | { type: "TRADE"; payload: MarketTrade }
  | { type: "BAR"; payload: MarketBar }
  | { type: "LIQUIDATION"; payload: LiquidationEvent }
  | { type: "SIGNAL_PREVIEW"; payload: StrategySignalPreview }
  | { type: "GATE_DECISION"; payload: GateDecision }
  | { type: "TRADE_ACTION"; payload: TradeActionEvidence }
  | { type: "EXECUTION_REPORT"; payload: ExecutionReport }
  | { type: "POSITIONS"; payload: PositionSnapshot[] }
  | { type: "OPEN_ORDERS"; payload: OpenOrderSnapshot[] }
  | { type: "ORDER_EVENT"; payload: OrderEvent }
  | { type: "FILL_EVENT"; payload: FillEvent }
  | { type: "ACCOUNT"; payload: AccountSnapshot }
  | { type: "ASSETS"; payload: AssetSnapshot[] }
  | { type: "QUANT_LEVELS"; payload: QuantLevelsContext }
  | { type: "TICK_TO_TRADE"; payload: TickToTradeTrace }
  | { type: "RUNTIME_HEALTH"; payload: RuntimeHealth }
  | { type: "SNAPSHOT"; payload: Partial<TradeHudState> }
  | { type: "SET_MODE"; payload: "paper" | "live" | "backtest" }
  | { type: "SET_BACKEND"; payload: boolean };

// ─── Limits ────────────────────────────────────────────────────────────────────

export const MAX_TRADES = 500;
export const MAX_ORDER_EVENTS = 500;
export const MAX_FILLS = 500;
export const MAX_BARS = 1000;
export const MAX_LIQUIDATIONS = 100;
export const MAX_SIGNAL_MARKERS = 200;
export const MAX_GATE_MARKERS = 200;
export const MAX_EXECUTION_MARKERS = 200;
export const HEATMAP_TIME_COLS = 360;
export const HEATMAP_PRICE_ROWS = 160;
