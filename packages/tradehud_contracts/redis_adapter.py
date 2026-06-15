"""Redis Stream adapter for TradeHUD — read-only ND runtime event consumer.

Reads observational runtime events from Nautilus-Daedalus Redis Streams
and converts them into TradeHUD contract models for SSE delivery.

SAFETY BOUNDARIES:
- READ-ONLY: uses XREAD/XREVRANGE only. Never XADD, never publish, never write.
- No credentials exposed. Redis URL stays server-side only.
- No order authority. No submit_order. No TradeAction creation.
- Graceful fallback: if Redis unavailable, returns None → caller falls back to mock.
- Missing numeric fields become None, never 0 (missing != true_zero).

Source selection:
- TRADEHUD_FEED_SOURCE=redis → adapter activates (if REDIS_URL configured)
- TRADEHUD_FEED_SOURCE=mock (default) → adapter does NOT activate
- REDIS_URL alone does NOT activate the adapter.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from packages.tradehud_contracts.config import TradeHudRedisConfig
from packages.tradehud_contracts.normalizer import (
    parse_stream_fields,
    to_optional_float,
    to_optional_int,
    to_optional_str,
    unwrap_payload,
    detect_force_liquidation,
    detect_trade_flags,
    requires_fields,
)
from packages.tradehud_contracts.stream_health import StreamHealthTracker
from packages.tradehud_contracts.models import (
    AccountSnapshotModel,
    BookLevelModel,
    ExecutionReportModel,
    GateDecisionModel,
    MarketBookL2Model,
    MarketBookTopModel,
    MarketTradeModel,
    OpenOrderSnapshotModel,
    PositionSnapshotModel,
    QuantLevelModel,
    QuantLevelsContextModel,
    RuntimeHealthModel,
    LaneHealthModel,
    StrategySignalPreviewModel,
    TickToTradeTraceModel,
    TradeActionEvidenceModel,
    TradeHudSnapshot,
)

logger = logging.getLogger(__name__)

# Reverse map: redis_stream_key → logical_name
def _build_reverse_map(config: TradeHudRedisConfig) -> dict[str, str]:
    return {v: k for k, v in config.get_stream_map().items()}


# ─── Model parsers ─────────────────────────────────────────────────────────────

def _ns() -> int:
    return int(time.time() * 1_000_000_000)


def _parse_book_top(data: dict[str, Any]) -> MarketBookTopModel | None:
    bid = to_optional_float(data.get("bid_price"))
    ask = to_optional_float(data.get("ask_price"))
    if bid is None or ask is None:
        return None  # Missing critical fields — not zero-filled
    ts = to_optional_int(data.get("ts_event_ns"))
    if ts is None:
        return None
    return MarketBookTopModel(
        symbol=to_optional_str(data.get("symbol")) or "UNKNOWN",
        bid_price=bid,
        ask_price=ask,
        bid_size=to_optional_float(data.get("bid_size")),
        ask_size=to_optional_float(data.get("ask_size")),
        mid_price=to_optional_float(data.get("mid_price")) or ((bid + ask) / 2),
        spread=to_optional_float(data.get("spread")) or (ask - bid),
        spread_bps=to_optional_float(data.get("spread_bps")),
        microprice=to_optional_float(data.get("microprice")) or ((bid + ask) / 2),
        ts_event_ns=ts,
        source_available=True,
        last_update_ts_ns=ts,
        receive_ts_ns=_ns(),
        stale=False,
        missing=False,
        provenance="redis",
        source_status="live",
    )


def _parse_book_l2(data: dict[str, Any]) -> MarketBookL2Model | None:
    bids_raw = data.get("bids", [])
    asks_raw = data.get("asks", [])
    if not bids_raw and not asks_raw:
        return None
    bids = []
    for b in bids_raw:
        bp = to_optional_float(b.get("price"))
        bs = to_optional_float(b.get("size"))
        if bp is None or bs is None:
            continue
        bids.append(BookLevelModel(
            price=bp, size=bs,
            total=to_optional_float(b.get("total")),
            age_ms=to_optional_int(b.get("age_ms")),
            source=b.get("source", "redis"),
        ))
    asks = []
    for a in asks_raw:
        ap = to_optional_float(a.get("price"))
        asz = to_optional_float(a.get("size"))
        if ap is None or asz is None:
            continue
        asks.append(BookLevelModel(
            price=ap, size=asz,
            total=to_optional_float(a.get("total")),
            age_ms=to_optional_int(a.get("age_ms")),
            source=a.get("source", "redis"),
        ))
    ts = to_optional_int(data.get("ts_event_ns"))
    if ts is None:
        return None
    return MarketBookL2Model(
        symbol=to_optional_str(data.get("symbol")) or "UNKNOWN",
        bids=bids,
        asks=asks,
        spread=to_optional_float(data.get("spread")) or 0.0,
        spread_bps=to_optional_float(data.get("spread_bps")),
        microprice=to_optional_float(data.get("microprice")),
        top5_imbalance=to_optional_float(data.get("top5_imbalance")),
        checksum=to_optional_str(data.get("checksum")),
        ts_event_ns=ts,
        source_available=True,
        last_update_ts_ns=ts,
        receive_ts_ns=_ns(),
        stale=False,
        missing=False,
        provenance="redis",
        source_status="live",
    )


def _parse_trade(data: dict[str, Any]) -> MarketTradeModel | None:
    data = unwrap_payload(data)
    price = to_optional_float(data.get("price"))
    qty = to_optional_float(data.get("qty"))
    ts = to_optional_int(data.get("ts_event_ns"))

    # Required fields — missing price/qty/ts = invalid record
    if price is None or qty is None or ts is None:
        return None

    is_liq, liq_side = detect_force_liquidation(data)
    flags = detect_trade_flags(data)
    side_raw = to_optional_str(data.get("side")) or "unknown"
    aggressor_raw = to_optional_str(data.get("aggressor")) or "unknown"

    return MarketTradeModel(
        trade_id=to_optional_str(data.get("trade_id"))
        or f"{ts or _ns()}-{price}",
        symbol=to_optional_str(data.get("symbol")) or "UNKNOWN",
        price=price,
        qty=qty,
        notional=to_optional_float(data.get("notional")) or (price * qty),
        side=side_raw.lower() if side_raw.lower() in ("buy", "sell") else "buy",
        aggressor=aggressor_raw.lower() if aggressor_raw.lower() in ("buy", "sell") else "unknown",
        source="redis",
        is_large_trade=flags["is_large_trade"],
        is_sweep=flags["is_sweep"],
        is_liquidation=is_liq,
        liq_side=liq_side,  # type: ignore
        ts_event_ns=ts,
        source_available=True,
        last_update_ts_ns=ts,
        receive_ts_ns=_ns(),
        stale=False,
        missing=False,
        provenance="redis",
        source_status="live",
    )


def _parse_account(data: dict[str, Any]) -> AccountSnapshotModel | None:
    bal = to_optional_float(data.get("balance"))
    if bal is None:
        return None
    ts = to_optional_int(data.get("ts_event_ns"))
    if ts is None:
        return None
    return AccountSnapshotModel(
        account_id=to_optional_str(data.get("account_id")) or "unknown",
        venue=to_optional_str(data.get("venue")) or "UNKNOWN",
        balance=bal,
        equity=to_optional_float(data.get("equity")) or bal,
        available_margin=to_optional_float(data.get("available_margin")),
        margin_used=to_optional_float(data.get("margin_used")),
        unrealized_pnl=to_optional_float(data.get("unrealized_pnl")),
        realized_pnl=to_optional_float(data.get("realized_pnl")),
        currency=to_optional_str(data.get("currency")) or "USDT",
        ts_event_ns=ts,
        source_available=True,
        last_update_ts_ns=ts,
        receive_ts_ns=_ns(),
        stale=False,
        missing=False,
        provenance="redis",
        source_status="live",
    )


def _parse_positions(data: dict[str, Any]) -> list[PositionSnapshotModel]:
    raw = data.get("positions", data)
    if isinstance(raw, str):
        import json as _json
        try:
            raw = _json.loads(raw)
        except Exception:
            return []
    if isinstance(raw, dict):
        raw = [raw]
    if not isinstance(raw, list):
        return []
    positions = []
    for p in raw:
        qty = to_optional_float(p.get("qty"))
        if qty is None:
            continue
        ts = to_optional_int(p.get("ts_event_ns"))
        if ts is None:
            continue
        positions.append(PositionSnapshotModel(
            symbol=to_optional_str(p.get("symbol")) or "UNKNOWN",
            venue=to_optional_str(p.get("venue")) or "UNKNOWN",
            side=to_optional_str(p.get("side")) or "flat",
            qty=qty,
            entry_price=to_optional_float(p.get("entry_price")),
            mark_price=to_optional_float(p.get("mark_price")),
            unrealized_pnl=to_optional_float(p.get("unrealized_pnl")),
            realized_pnl=to_optional_float(p.get("realized_pnl")),
            margin=to_optional_float(p.get("margin")),
            ts_event_ns=ts,
            source_available=True,
            last_update_ts_ns=ts,
            receive_ts_ns=_ns(),
            stale=False,
            missing=False,
            provenance="redis",
            source_status="live",
        ))
    return positions


def _parse_open_orders(data: dict[str, Any]) -> list[OpenOrderSnapshotModel]:
    raw = data.get("orders", data)
    if isinstance(raw, dict):
        raw = [raw]
    if not isinstance(raw, list):
        return []
    orders = []
    for o in raw:
        price = to_optional_float(o.get("price"))
        if price is None:
            continue
        ts = to_optional_int(o.get("ts_event_ns"))
        if ts is None:
            continue
        qty = to_optional_float(o.get("qty"))
        if qty is None:
            continue
        filled_qty = to_optional_float(o.get("filled_qty"))
        orders.append(OpenOrderSnapshotModel(
            order_id=to_optional_str(o.get("order_id")) or "unknown",
            client_order_id=to_optional_str(o.get("client_order_id")) or "unknown",
            symbol=to_optional_str(o.get("symbol")) or "UNKNOWN",
            venue=to_optional_str(o.get("venue")) or "UNKNOWN",
            side=to_optional_str(o.get("side")) or "buy",
            order_type=to_optional_str(o.get("order_type")) or "LIMIT",
            price=price,
            qty=qty,
            filled_qty=filled_qty if filled_qty is not None else 0.0,
            status=to_optional_str(o.get("status")) or "LIVE",
            ts_event_ns=ts,
            source_available=True,
            last_update_ts_ns=ts,
            receive_ts_ns=_ns(),
            stale=False,
            missing=False,
            provenance="redis",
            source_status="live",
        ))
    return orders


def _parse_signal(data: dict[str, Any]) -> StrategySignalPreviewModel | None:
    conf = to_optional_float(data.get("confidence_score"))
    if conf is None:
        return None
    ts = to_optional_int(data.get("ts_event_ns"))
    if ts is None:
        return None
    return StrategySignalPreviewModel(
        signal_id=to_optional_str(data.get("signal_id")) or "unknown",
        symbol=to_optional_str(data.get("symbol")) or "UNKNOWN",
        feature_hash=to_optional_str(data.get("feature_hash")) or "",
        context_hash=to_optional_str(data.get("context_hash")) or "",
        policy_hash=to_optional_str(data.get("policy_hash")) or "",
        graph_trace_hash=to_optional_str(data.get("graph_trace_hash")) or "",
        confidence_score=conf,
        direction=to_optional_str(data.get("direction")) or "flat",
        target_hint=to_optional_float(data.get("target_hint")),
        invalidation_hint=to_optional_float(data.get("invalidation_hint")),
        size_hint=to_optional_float(data.get("size_hint")),
        preview_note=to_optional_str(data.get("preview_note")) or "Preview only — NOT EXECUTABLE",
        ts_event_ns=ts,
        source_available=True,
        last_update_ts_ns=ts,
        receive_ts_ns=_ns(),
        stale=False,
        missing=False,
        provenance="redis",
        source_status="live",
    )


def _parse_gate(data: dict[str, Any]) -> GateDecisionModel | None:
    decision = to_optional_str(data.get("decision"))
    if decision is None:
        return None
    ts = to_optional_int(data.get("ts_event_ns"))
    if ts is None:
        return None
    return GateDecisionModel(
        decision_id=to_optional_str(data.get("decision_id")) or "unknown",
        decision=decision,
        first_blocking_gate=to_optional_str(data.get("first_blocking_gate")),
        reason_code=to_optional_str(data.get("reason_code")) or "",
        confidence_delta=to_optional_float(data.get("confidence_delta")),
        size_modifier=to_optional_float(data.get("size_modifier")) or 1.0,
        target_hint=to_optional_float(data.get("target_hint")),
        invalidation_hint=to_optional_float(data.get("invalidation_hint")),
        gate_decision_hash=to_optional_str(data.get("gate_decision_hash")) or "",
        source_signal_hash=to_optional_str(data.get("source_signal_hash")) or "",
        ts_event_ns=ts,
        source_available=True,
        last_update_ts_ns=ts,
        receive_ts_ns=_ns(),
        stale=False,
        missing=False,
        provenance="redis",
        source_status="live",
    )


def _parse_trade_action(data: dict[str, Any]) -> TradeActionEvidenceModel | None:
    action = to_optional_str(data.get("action"))
    if action is None:
        return None
    price = to_optional_float(data.get("price"))
    qty = to_optional_float(data.get("qty"))
    ts = to_optional_int(data.get("ts_event_ns"))
    trade_action_hash = to_optional_str(data.get("trade_action_hash"))
    source_gate_decision_hash = to_optional_str(data.get("source_gate_decision_hash"))
    if price is None or qty is None or ts is None:
        return None
    if not trade_action_hash:
        return None
    if not source_gate_decision_hash:
        return None
    return TradeActionEvidenceModel(
        action_id=to_optional_str(data.get("action_id")) or "unknown",
        action=action,
        side=to_optional_str(data.get("side")) or "buy",
        price=price,
        qty=qty,
        trade_action_hash=trade_action_hash,
        source_gate_decision_hash=source_gate_decision_hash,
        created_by=to_optional_str(data.get("created_by")) or "run_gate_engine",
        ts_event_ns=ts,
        source_available=True,
        last_update_ts_ns=ts,
        receive_ts_ns=_ns(),
        stale=False,
        missing=False,
        provenance="redis",
        source_status="live",
    )


def _parse_execution(data: dict[str, Any]) -> ExecutionReportModel | None:
    status = to_optional_str(data.get("status"))
    if status is None:
        return None
    submit_ts = to_optional_int(data.get("submit_ts_ns"))
    if submit_ts is None:
        return None
    ts = to_optional_int(data.get("ts_event_ns"))
    if ts is None:
        return None
    return ExecutionReportModel(
        report_id=to_optional_str(data.get("report_id")) or "unknown",
        status=status,
        exchange_order_id=to_optional_str(data.get("exchange_order_id")),
        client_order_id=to_optional_str(data.get("client_order_id")) or "unknown",
        trade_action_hash=to_optional_str(data.get("trade_action_hash")) or "",
        symbol=to_optional_str(data.get("symbol")) or "UNKNOWN",
        side=to_optional_str(data.get("side")) or "buy",
        filled_qty=to_optional_float(data.get("filled_qty")) or 0,
        avg_fill_price=to_optional_float(data.get("avg_fill_price")),
        submit_ts_ns=submit_ts,
        ack_ts_ns=to_optional_int(data.get("ack_ts_ns")),
        fill_ts_ns=to_optional_int(data.get("fill_ts_ns")),
        submit_to_ack_us=to_optional_int(data.get("submit_to_ack_us")),
        ack_to_fill_us=to_optional_int(data.get("ack_to_fill_us")),
        rejection_reason=to_optional_str(data.get("rejection_reason")),
        ts_event_ns=ts,
        source_available=True,
        last_update_ts_ns=ts,
        receive_ts_ns=_ns(),
        stale=False,
        missing=False,
        provenance="redis",
        source_status="live",
    )


def _parse_quant_levels(data: dict[str, Any]) -> QuantLevelsContextModel | None:
    levels_raw = data.get("levels", [])
    if not levels_raw:
        return None
    levels = []
    for l in levels_raw:
        lp = to_optional_float(l.get("price"))
        if lp is None:
            continue
        levels.append(QuantLevelModel(
            label=l.get("label", ""),
            price=lp,
            kind=l.get("kind", "pivot"),
        ))
    ts = to_optional_int(data.get("ts_event_ns"))
    if ts is None:
        return None
    return QuantLevelsContextModel(
        symbol=to_optional_str(data.get("symbol")) or "UNKNOWN",
        levels=levels,
        ts_event_ns=ts,
        source_available=True,
        last_update_ts_ns=ts,
        receive_ts_ns=_ns(),
        stale=False,
        missing=False,
        provenance="redis",
        source_status="live",
    )


def _parse_tick_to_trade(data: dict[str, Any]) -> TickToTradeTraceModel | None:
    total = to_optional_int(data.get("total_tick_to_trade_us"))
    if total is None:
        return None
    ts = to_optional_int(data.get("ts_event_ns"))
    if ts is None:
        return None
    tick_recv = to_optional_int(data.get("tick_receive_ts_ns"))
    sig_ts = to_optional_int(data.get("signal_ts_ns"))
    gate_ts = to_optional_int(data.get("gate_ts_ns"))
    exec_ts = to_optional_int(data.get("execution_ts_ns"))
    if any(v is None for v in (tick_recv, sig_ts, gate_ts, exec_ts)):
        return None
    return TickToTradeTraceModel(
        trace_id=to_optional_str(data.get("trace_id")) or "unknown",
        tick_receive_ts_ns=tick_recv,
        signal_ts_ns=sig_ts,
        gate_ts_ns=gate_ts,
        execution_ts_ns=exec_ts,
        tick_to_signal_us=to_optional_int(data.get("tick_to_signal_us")) or 0,
        signal_to_gate_us=to_optional_int(data.get("signal_to_gate_us")) or 0,
        gate_to_execution_us=to_optional_int(data.get("gate_to_execution_us")) or 0,
        total_tick_to_trade_us=total,
        ts_event_ns=ts,
        source_available=True,
        last_update_ts_ns=ts,
        receive_ts_ns=_ns(),
        stale=False,
        missing=False,
        provenance="redis",
        source_status="live",
    )


def _parse_runtime_health(data: dict[str, Any]) -> RuntimeHealthModel | None:
    def _lane(prefix: str) -> LaneHealthModel:
        return LaneHealthModel(
            lane=data.get(f"{prefix}_lane", prefix),
            status=data.get(f"{prefix}_status", "unknown"),
            last_heartbeat_ts_ns=to_optional_int(data.get(f"{prefix}_heartbeat_ns")),
            age_ms=to_optional_int(data.get(f"{prefix}_age_ms")),
            stale=bool(data.get(f"{prefix}_stale", False)),
            missing=bool(data.get(f"{prefix}_missing", False)),
            reason_code=to_optional_str(data.get(f"{prefix}_reason")),
        )
    ts = to_optional_int(data.get("ts_event_ns"))
    if ts is None:
        return None
    return RuntimeHealthModel(
        run_main_strategy_signal=_lane("main_strategy"),
        run_gate_engine=_lane("gate_engine"),
        run_execution_lane=_lane("execution_lane"),
        ai_lane_advisory=_lane("ai_advisory"),
        data_health=_lane("data"),
        ts_event_ns=ts,
        source_available=True,
        last_update_ts_ns=ts,
        receive_ts_ns=_ns(),
        stale=False,
        missing=False,
        provenance="redis",
        source_status="live",
    )


# Parser dispatch: logical_name → (snapshot_field, parser_fn)
_PARSERS: dict[str, tuple[str, Any]] = {
    "book_top": ("book_top", _parse_book_top),
    "book_l2": ("book_l2", _parse_book_l2),
    "trades": ("trades", _parse_trade),
    "account": ("account", _parse_account),
    "positions": ("positions", _parse_positions),
    "orders": ("open_orders", _parse_open_orders),
    "signal": ("latest_signal_preview", _parse_signal),
    "gate": ("latest_gate_decision", _parse_gate),
    "trade_action": ("latest_trade_action", _parse_trade_action),
    "execution": ("latest_execution_report", _parse_execution),
    "quant_levels": ("quant_levels", _parse_quant_levels),
    "tick_to_trade": ("tick_to_trade", _parse_tick_to_trade),
    "health": ("runtime_health", _parse_runtime_health),
}


def parse_stream_entry(logical_name: str, fields: dict[bytes, bytes]) -> tuple[str, Any] | None:
    """Parse a Redis stream entry into a (field_name, model) tuple."""
    if logical_name not in _PARSERS:
        return None
    field_name, parser = _PARSERS[logical_name]
    data = parse_stream_fields(fields)
    result = parser(data)
    if result is None:
        return None
    return field_name, result


def build_snapshot_from_redis(entries: dict[str, dict[bytes, bytes]]) -> TradeHudSnapshot:
    """Build a TradeHudSnapshot from collected Redis stream entries."""
    snapshot_fields: dict[str, Any] = {}
    for suffix, fields in entries.items():
        parsed = parse_stream_entry(suffix, fields)
        if parsed:
            field_name, model = parsed
            snapshot_fields[field_name] = model
    snapshot = TradeHudSnapshot(**snapshot_fields)
    snapshot.provenance = "redis"
    return snapshot


class RedisStreamAdapter:
    """Read-only Redis Stream consumer for ND runtime TradeHUD events.

    Uses ONE multi-stream XREAD call covering all configured streams.
    Seeds initial state via XREVRANGE on startup.
    Tracks per-stream health.
    Never writes to Redis. Never exposes credentials.

    Usage:
        config = TradeHudRedisConfig.from_env()
        adapter = RedisStreamAdapter(config)
        if await adapter.connect():
            snapshot = await adapter.get_snapshot()
    """

    def __init__(self, config: TradeHudRedisConfig | None = None) -> None:
        self._config = config or TradeHudRedisConfig.from_env()
        self._client = None
        self._last_ids: dict[str, str] = {}  # per-stream last consumed ID (by stream_key)
        self._cached: dict[str, dict[bytes, bytes] | None] = {}  # latest cached per logical_name
        self._trades_buffer: list[MarketTradeModel] = []
        self._connected = False
        self._connect_error: str | None = None
        self._health = StreamHealthTracker(self._config)
        self._reverse_map = _build_reverse_map(self._config)

        # Initialize last_ids to "$" (latest only) for all streams
        for logical_name, stream_key in self._config.get_stream_map().items():
            self._last_ids[stream_key] = "$"
            self._cached[logical_name] = None

    async def connect(self) -> bool:
        """Attempt to connect to Redis. Returns True if connected."""
        if not self._config.is_redis_enabled:
            self._connected = False
            self._connect_error = "feed_source is not redis"
            return False
        if not self._config.is_redis_configured:
            self._connected = False
            self._connect_error = "No REDIS_URL configured"
            return False

        try:
            import redis.asyncio as aioredis
            self._client = aioredis.from_url(
                self._config.redis_url,
                decode_responses=False,
                socket_connect_timeout=2,
                socket_timeout=2,
                retry_on_timeout=True,
            )
            await self._client.ping()
            self._connected = True
            self._connect_error = None
            self._health.mark_connected(True)
            logger.info("RedisStreamAdapter connected to Redis (namespace=%s)", self._config.stream_namespace)
            # Seed initial state
            await self._seed_initial_state()
            return True
        except ImportError:
            self._connected = False
            self._connect_error = "redis package not installed"
            logger.warning("redis package not installed — adapter disabled")
            return False
        except Exception as e:
            self._connected = False
            self._connect_error = str(e)
            self._health.mark_connected(False)
            logger.warning("Redis connection failed: %s — falling back to mock", e)
            self._client = None
            return False

    async def _seed_initial_state(self) -> None:
        """Seed initial cache with latest entry per stream via XREVRANGE."""
        if not self.is_connected():
            return
        stream_map = self._config.get_stream_map()
        for logical_name, stream_key in stream_map.items():
            try:
                result = await self._client.xrevrange(stream_key, count=1)
                if result:
                    entry_id, fields = result[0]
                    entry_id_str = entry_id.decode() if isinstance(entry_id, bytes) else str(entry_id)
                    self._last_ids[stream_key] = entry_id_str
                    self._cached[logical_name] = dict(fields)
                    event_ts = None
                    parsed_fields = parse_stream_fields(dict(fields))
                    event_ts = to_optional_int(parsed_fields.get("ts_event_ns"))
                    self._health.record_seed(logical_name, entry_id_str, event_ts)
                else:
                    self._health.record_seed(logical_name, None, None)
            except Exception as e:
                logger.debug("XREVRANGE failed for %s: %s", stream_key, e)
                self._health.record_error(logical_name, str(e))

    async def disconnect(self) -> None:
        if self._client:
            try:
                await self._client.aclose()
            except Exception:
                pass
            self._client = None
        self._connected = False
        self._health.mark_connected(False)

    def is_connected(self) -> bool:
        return self._connected and self._client is not None

    def is_configured(self) -> bool:
        return self._config.is_redis_configured

    def get_connect_error(self) -> str | None:
        return self._connect_error

    async def _multi_stream_xread(self) -> dict[str, dict[bytes, bytes]]:
        """ONE multi-stream XREAD covering all configured streams.

        Returns dict mapping logical_name → entry fields.
        """
        if not self.is_connected():
            return {}

        stream_map = self._config.get_stream_map()
        # Build the streams dict for XREAD: {stream_key: last_id}
        xread_streams: dict[str, str] = {}
        for logical_name, stream_key in stream_map.items():
            xread_streams[stream_key] = self._last_ids.get(stream_key, "$")

        try:
            result = await self._client.xread(
                xread_streams,
                count=self._config.redis_count,
                block=self._config.redis_block_ms,
            )
        except Exception as e:
            logger.warning("Multi-stream XREAD failed: %s", e)
            self._health.mark_connected(False)
            return {}

        if not result:
            return {}

        fresh: dict[str, dict[bytes, bytes]] = {}
        for stream_key_bytes, entries in result:
            stream_key = stream_key_bytes.decode() if isinstance(stream_key_bytes, bytes) else str(stream_key_bytes)
            logical_name = self._reverse_map.get(stream_key)
            if not logical_name:
                continue
            for entry_id, fields in entries:
                entry_id_str = entry_id.decode() if isinstance(entry_id, bytes) else str(entry_id)
                self._last_ids[stream_key] = entry_id_str
                field_dict = dict(fields)
                self._cached[logical_name] = field_dict
                fresh[logical_name] = field_dict

                # Update health
                parsed_fields = parse_stream_fields(field_dict)
                event_ts = to_optional_int(parsed_fields.get("ts_event_ns"))
                self._health.record_event(logical_name, entry_id_str, event_ts)

                # Buffer trades
                if logical_name == "trades":
                    trade = _parse_trade(parsed_fields)
                    if trade:
                        self._trades_buffer.append(trade)
                        if len(self._trades_buffer) > 500:
                            self._trades_buffer = self._trades_buffer[-500:]

        return fresh

    async def get_snapshot(self, symbol: str | None = None) -> TradeHudSnapshot | None:
        """Build a TradeHudSnapshot from latest Redis stream data."""
        entries = await self._multi_stream_xread()
        # Merge fresh entries with cached for all streams
        merged: dict[str, dict[bytes, bytes]] = {}
        for logical_name in self._config.get_stream_map():
            if logical_name in entries:
                merged[logical_name] = entries[logical_name]
            elif self._cached.get(logical_name):
                merged[logical_name] = self._cached[logical_name]

        if not merged:
            return None

        snapshot_fields: dict[str, Any] = {}
        for logical_name, fields in merged.items():
            if logical_name not in _PARSERS:
                continue
            field_name, parser = _PARSERS[logical_name]
            parsed_fields = parse_stream_fields(fields)
            result = parser(parsed_fields)
            if result is not None:
                snapshot_fields[field_name] = result

        # Add buffered trades
        if self._trades_buffer:
            snapshot_fields["trades"] = list(self._trades_buffer)

        if not snapshot_fields:
            return None

        snapshot = TradeHudSnapshot(**snapshot_fields)
        snapshot.provenance = "redis"
        return snapshot

    async def get_health(self) -> dict[str, Any]:
        """Return adapter health status."""
        health_eval = self._health.evaluate()
        return {
            "status": "connected" if self.is_connected() else "disconnected",
            "feed_source": self._config.feed_source,
            "redis_configured": self._config.is_redis_configured,
            "redis_connected": self.is_connected(),
            "has_runtime": self.is_connected(),
            "has_redis": self.is_connected(),
            "has_postgres": False,
            "mode": "redis" if self.is_connected() else "mock",
            "provenance": "redis" if self.is_connected() else "mock",
            "error": self._connect_error,
            "stream_namespace": self._config.stream_namespace,
            "stream_health": health_eval,
        }
