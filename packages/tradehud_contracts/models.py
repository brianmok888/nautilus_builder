"""TradeHUD Pydantic models — observational runtime monitoring contracts.

All responses are read-only evidence snapshots.
No submit_order. No TradeAction creation. No exchange credentials.
"""

from __future__ import annotations

from typing import Literal, Optional
from pydantic import BaseModel, Field


# ─── Freshness metadata ────────────────────────────────────────────────────────

SourceStatus = Literal[
    "live", "stale", "missing", "synthetic", "true_zero", "unavailable", "unknown"
]


class SourceFreshnessMeta(BaseModel):
    source_available: bool = False
    last_update_ts_ns: int | None = None
    receive_ts_ns: int | None = None
    age_ms: int | None = None
    stale: bool = True
    missing: bool = True
    true_zero: bool = False
    provenance: str = "unknown"
    source_status: SourceStatus = "unknown"


# ─── Market data ───────────────────────────────────────────────────────────────

class MarketBookTopModel(SourceFreshnessMeta):
    symbol: str
    bid_price: float
    ask_price: float
    bid_size: float
    ask_size: float
    mid_price: float
    spread: float
    spread_bps: float
    microprice: float
    ts_event_ns: int


class BookLevelModel(BaseModel):
    price: float
    size: float
    total: float
    age_ms: int
    source: str = "mock"


class MarketBookL2Model(SourceFreshnessMeta):
    symbol: str
    bids: list[BookLevelModel]
    asks: list[BookLevelModel]
    spread: float
    spread_bps: float
    microprice: float
    top5_imbalance: float
    checksum: str | None = None
    ts_event_ns: int


class MarketTradeModel(SourceFreshnessMeta):
    trade_id: str
    symbol: str
    price: float
    qty: float
    notional: float
    side: Literal["buy", "sell"]
    aggressor: Literal["buy", "sell", "unknown"]
    source: str = "mock"
    is_large_trade: bool = False
    is_sweep: bool = False
    is_liquidation: bool = False
    liq_side: Literal["long_liq", "short_liq"] | None = None
    ts_event_ns: int


# ─── ND evidence types ─────────────────────────────────────────────────────────

class StrategySignalPreviewModel(SourceFreshnessMeta):
    signal_id: str
    symbol: str
    feature_hash: str
    context_hash: str
    policy_hash: str
    graph_trace_hash: str
    confidence_score: float
    direction: Literal["long", "short", "flat"]
    target_hint: float | None = None
    invalidation_hint: float | None = None
    size_hint: float | None = None
    preview_note: str = "Preview only — NOT EXECUTABLE"
    ts_event_ns: int


class GateDecisionModel(SourceFreshnessMeta):
    decision_id: str
    decision: Literal["APPROVED", "HOLD", "REJECTED"]
    first_blocking_gate: str | None = None
    reason_code: str
    confidence_delta: float
    size_modifier: float
    target_hint: float | None = None
    invalidation_hint: float | None = None
    gate_decision_hash: str
    source_signal_hash: str
    ts_event_ns: int


class TradeActionEvidenceModel(SourceFreshnessMeta):
    action_id: str
    action: str
    side: Literal["buy", "sell"]
    price: float
    qty: float
    trade_action_hash: str
    source_gate_decision_hash: str
    created_by: str = "run_gate_engine"
    ts_event_ns: int


class ExecutionReportModel(SourceFreshnessMeta):
    report_id: str
    status: Literal[
        "SUBMITTED", "ACKED", "LIVE", "PARTIAL_FILL", "FILLED", "CANCELED", "REJECTED", "EXPIRED"
    ]
    exchange_order_id: str | None = None
    client_order_id: str
    trade_action_hash: str
    symbol: str
    side: Literal["buy", "sell"]
    filled_qty: float = 0
    avg_fill_price: float | None = None
    submit_ts_ns: int
    ack_ts_ns: int | None = None
    fill_ts_ns: int | None = None
    submit_to_ack_us: int | None = None
    ack_to_fill_us: int | None = None
    rejection_reason: str | None = None
    ts_event_ns: int


# ─── Account / positions / orders ──────────────────────────────────────────────

class AccountSnapshotModel(SourceFreshnessMeta):
    account_id: str
    venue: str
    balance: float
    equity: float
    available_margin: float
    margin_used: float
    unrealized_pnl: float
    realized_pnl: float
    currency: str = "USDT"
    ts_event_ns: int


class PositionSnapshotModel(SourceFreshnessMeta):
    symbol: str
    venue: str
    side: Literal["long", "short", "flat"]
    qty: float
    entry_price: float
    mark_price: float
    unrealized_pnl: float
    realized_pnl: float
    margin: float
    ts_event_ns: int


class OpenOrderSnapshotModel(SourceFreshnessMeta):
    order_id: str
    client_order_id: str
    symbol: str
    venue: str
    side: Literal["buy", "sell"]
    order_type: str
    price: float
    qty: float
    filled_qty: float = 0
    status: str = "LIVE"
    ts_event_ns: int


class AssetSnapshotModel(SourceFreshnessMeta):
    asset: str
    free: float
    locked: float
    usd_value: float


# ─── Quant / latency / health ──────────────────────────────────────────────────

class QuantLevelModel(BaseModel):
    label: str
    price: float
    kind: Literal["support", "resistance", "pivot"]


class QuantLevelsContextModel(SourceFreshnessMeta):
    symbol: str
    levels: list[QuantLevelModel]
    ts_event_ns: int


class TickToTradeTraceModel(SourceFreshnessMeta):
    trace_id: str
    tick_receive_ts_ns: int
    signal_ts_ns: int
    gate_ts_ns: int
    execution_ts_ns: int
    tick_to_signal_us: int
    signal_to_gate_us: int
    gate_to_execution_us: int
    total_tick_to_trade_us: int
    ts_event_ns: int


class LaneHealthModel(BaseModel):
    lane: str
    status: Literal["healthy", "stale", "missing", "degraded", "unknown"]
    last_heartbeat_ts_ns: int | None = None
    age_ms: int | None = None
    stale: bool = False
    missing: bool = False
    reason_code: str | None = None


class RuntimeHealthModel(SourceFreshnessMeta):
    run_main_strategy_signal: LaneHealthModel
    run_gate_engine: LaneHealthModel
    run_execution_lane: LaneHealthModel
    ai_lane_advisory: LaneHealthModel
    data_health: LaneHealthModel
    ts_event_ns: int


# ─── Aggregate snapshot ────────────────────────────────────────────────────────

class TradeHudSnapshot(BaseModel):
    """Complete observational snapshot for TradeHUD display."""

    book_top: MarketBookTopModel | None = None
    book_l2: MarketBookL2Model | None = None
    latest_signal_preview: StrategySignalPreviewModel | None = None
    latest_gate_decision: GateDecisionModel | None = None
    latest_trade_action: TradeActionEvidenceModel | None = None
    latest_execution_report: ExecutionReportModel | None = None
    account: AccountSnapshotModel | None = None
    positions: list[PositionSnapshotModel] = Field(default_factory=list)
    trades: list[MarketTradeModel] = Field(default_factory=list)
    open_orders: list[OpenOrderSnapshotModel] = Field(default_factory=list)
    assets: list[AssetSnapshotModel] = Field(default_factory=list)
    quant_levels: QuantLevelsContextModel | None = None
    tick_to_trade: TickToTradeTraceModel | None = None
    runtime_health: RuntimeHealthModel | None = None
    provenance: str = "mock"
