"""Redis Stream adapter for TradeHUD — read-only ND runtime event consumer.

Reads observational runtime events from Nautilus-Daedalus Redis Streams
and converts them into TradeHUD contract models for SSE delivery.

SAFETY BOUNDARIES:
- READ-ONLY: uses XREAD only. Never XADD, never publish, never write.
- No credentials exposed. Redis URL stays server-side only.
- No order authority. No submit_order. No TradeAction creation.
- No write to Redis. No write to PostgreSQL. No exchange calls.
- Graceful fallback: if Redis unavailable, returns None → caller falls back to mock.

Redis Stream naming convention (ND runtime → Redis Streams):
    nautilus:tradehud:book_top      — MarketBookTopModel events
    nautilus:tradehud:book_l2       — MarketBookL2Model events
    nautilus:tradehud:account       — AccountSnapshotModel events
    nautilus:tradehud:positions     — PositionSnapshotModel[] events
    nautilus:tradehud:open_orders   — OpenOrderSnapshotModel[] events
    nautilus:tradehud:signal        — StrategySignalPreviewModel events
    nautilus:tradehud:gate          — GateDecisionModel events
    nautilus:tradehud:trade_action  — TradeActionEvidenceModel events
    nautilus:tradehud:execution     — ExecutionReportModel events
    nautilus:tradehud:quant_levels  — QuantLevelsContextModel events
    nautilus:tradehud:tick_to_trade — TickToTradeTraceModel events
    nautilus:tradehud:runtime_health — RuntimeHealthModel events

Each stream entry is a Redis hash with fields matching the contract model.
The adapter reads the latest entry (XREAD BLOCK, last id) and converts to models.

This module NEVER imports from browser/frontend code.
Redis URL comes from environment variable REDIS_URL (server-side only).
"""

from __future__ import annotations

import json
import logging
import os
import time
from typing import Any

from packages.tradehud_contracts.models import (
    AccountSnapshotModel,
    AssetSnapshotModel,
    BookLevelModel,
    ExecutionReportModel,
    GateDecisionModel,
    MarketBookL2Model,
    MarketBookTopModel,
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

# Stream key prefix — must match ND runtime publisher convention.
_STREAM_PREFIX = "nautilus:tradehud:"

# Streams consumed by the adapter — all read-only XREAD.
_STREAM_KEYS: list[str] = [
    "book_top",
    "book_l2",
    "account",
    "positions",
    "open_orders",
    "signal",
    "gate",
    "trade_action",
    "execution",
    "quant_levels",
    "tick_to_trade",
    "runtime_health",
]

# Maximum entries to read per XREAD per stream.
_MAX_READ_COUNT = 1
# Block timeout for XREAD in milliseconds — keeps the read responsive.
_XREAD_BLOCK_MS = 500


def _get_redis_url() -> str | None:
    """Return Redis URL from environment. Server-side only — never browser-exposed."""
    return os.environ.get("REDIS_URL") or os.environ.get("REDIS_CONNECTION_STRING")


def _is_redis_configured() -> bool:
    """Check if Redis is configured without connecting."""
    return _get_redis_url() is not None


def _parse_stream_entry(fields: dict[bytes, bytes]) -> dict[str, Any]:
    """Parse a Redis stream entry hash into a Python dict.

    Redis stores hash fields as bytes; we decode keys and JSON-parse values
    that look like JSON objects/arrays.
    """
    result: dict[str, Any] = {}
    for key_b, val_b in fields.items():
        key = key_b.decode("utf-8") if isinstance(key_b, bytes) else str(key_b)
        val = val_b.decode("utf-8") if isinstance(val_b, bytes) else str(val_b)
        # Try JSON parse for complex types
        if val.startswith("{") or val.startswith("["):
            try:
                result[key] = json.loads(val)
            except (json.JSONDecodeError, ValueError):
                result[key] = val
        else:
            result[key] = val
    return result


def _to_int(val: Any, default: int = 0) -> int:
    """Safely convert to int."""
    try:
        return int(val)
    except (TypeError, ValueError):
        return default


def _to_float(val: Any, default: float = 0.0) -> float:
    """Safely convert to float."""
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


def _parse_book_top(data: dict[str, Any]) -> MarketBookTopModel | None:
    if "bid_price" not in data or "ask_price" not in data:
        return None
    try:
        return MarketBookTopModel(
            symbol=data.get("symbol", "UNKNOWN"),
            bid_price=_to_float(data.get("bid_price")),
            ask_price=_to_float(data.get("ask_price")),
            bid_size=_to_float(data.get("bid_size")),
            ask_size=_to_float(data.get("ask_size")),
            mid_price=_to_float(data.get("mid_price")),
            spread=_to_float(data.get("spread")),
            spread_bps=_to_float(data.get("spread_bps")),
            microprice=_to_float(data.get("microprice")),
            ts_event_ns=_to_int(data.get("ts_event_ns")),
            source_available=True,
            last_update_ts_ns=_to_int(data.get("ts_event_ns")),
            receive_ts_ns=int(time.time() * 1_000_000_000),
            stale=False,
            missing=False,
            provenance="redis",
            source_status="live",
        )
    except Exception as e:
        logger.warning("Failed to parse book_top: %s", e)
        return None


def _parse_book_l2(data: dict[str, Any]) -> MarketBookL2Model | None:
    try:
        bids_raw = data.get("bids", [])
        asks_raw = data.get("asks", [])
        bids = [
            BookLevelModel(
                price=_to_float(b.get("price")),
                size=_to_float(b.get("size")),
                total=_to_float(b.get("total")),
                age_ms=_to_int(b.get("age_ms")),
                source=b.get("source", "redis"),
            )
            for b in bids_raw
        ]
        asks = [
            BookLevelModel(
                price=_to_float(a.get("price")),
                size=_to_float(a.get("size")),
                total=_to_float(a.get("total")),
                age_ms=_to_int(a.get("age_ms")),
                source=a.get("source", "redis"),
            )
            for a in asks_raw
        ]
        return MarketBookL2Model(
            symbol=data.get("symbol", "UNKNOWN"),
            bids=bids,
            asks=asks,
            spread=_to_float(data.get("spread")),
            spread_bps=_to_float(data.get("spread_bps")),
            microprice=_to_float(data.get("microprice")),
            top5_imbalance=_to_float(data.get("top5_imbalance")),
            checksum=data.get("checksum"),
            ts_event_ns=_to_int(data.get("ts_event_ns")),
            source_available=True,
            last_update_ts_ns=_to_int(data.get("ts_event_ns")),
            receive_ts_ns=int(time.time() * 1_000_000_000),
            stale=False,
            missing=False,
            provenance="redis",
            source_status="live",
        )
    except Exception as e:
        logger.warning("Failed to parse book_l2: %s", e)
        return None


def _parse_account(data: dict[str, Any]) -> AccountSnapshotModel | None:
    try:
        return AccountSnapshotModel(
            account_id=data.get("account_id", "unknown"),
            venue=data.get("venue", "UNKNOWN"),
            balance=_to_float(data.get("balance")),
            equity=_to_float(data.get("equity")),
            available_margin=_to_float(data.get("available_margin")),
            margin_used=_to_float(data.get("margin_used")),
            unrealized_pnl=_to_float(data.get("unrealized_pnl")),
            realized_pnl=_to_float(data.get("realized_pnl")),
            currency=data.get("currency", "USDT"),
            ts_event_ns=_to_int(data.get("ts_event_ns")),
            source_available=True,
            last_update_ts_ns=_to_int(data.get("ts_event_ns")),
            receive_ts_ns=int(time.time() * 1_000_000_000),
            stale=False,
            missing=False,
            provenance="redis",
            source_status="live",
        )
    except Exception as e:
        logger.warning("Failed to parse account: %s", e)
        return None


def _parse_positions(data: dict[str, Any]) -> list[PositionSnapshotModel]:
    try:
        raw = data.get("positions", data)  # Accept either wrapper or direct list
        if isinstance(raw, dict):
            raw = [raw]
        if not isinstance(raw, list):
            return []
        positions = []
        for p in raw:
            positions.append(PositionSnapshotModel(
                symbol=p.get("symbol", "UNKNOWN"),
                venue=p.get("venue", "UNKNOWN"),
                side=p.get("side", "flat"),
                qty=_to_float(p.get("qty")),
                entry_price=_to_float(p.get("entry_price")),
                mark_price=_to_float(p.get("mark_price")),
                unrealized_pnl=_to_float(p.get("unrealized_pnl")),
                realized_pnl=_to_float(p.get("realized_pnl")),
                margin=_to_float(p.get("margin")),
                ts_event_ns=_to_int(p.get("ts_event_ns")),
                source_available=True,
                last_update_ts_ns=_to_int(p.get("ts_event_ns")),
                stale=False,
                missing=False,
                provenance="redis",
                source_status="live",
            ))
        return positions
    except Exception as e:
        logger.warning("Failed to parse positions: %s", e)
        return []


def _parse_open_orders(data: dict[str, Any]) -> list[OpenOrderSnapshotModel]:
    try:
        raw = data.get("orders", data)
        if isinstance(raw, dict):
            raw = [raw]
        if not isinstance(raw, list):
            return []
        orders = []
        for o in raw:
            orders.append(OpenOrderSnapshotModel(
                order_id=o.get("order_id", "unknown"),
                client_order_id=o.get("client_order_id", "unknown"),
                symbol=o.get("symbol", "UNKNOWN"),
                venue=o.get("venue", "UNKNOWN"),
                side=o.get("side", "buy"),
                order_type=o.get("order_type", "LIMIT"),
                price=_to_float(o.get("price")),
                qty=_to_float(o.get("qty")),
                filled_qty=_to_float(o.get("filled_qty", 0)),
                status=o.get("status", "LIVE"),
                ts_event_ns=_to_int(o.get("ts_event_ns")),
                source_available=True,
                last_update_ts_ns=_to_int(o.get("ts_event_ns")),
                stale=False,
                missing=False,
                provenance="redis",
                source_status="live",
            ))
        return orders
    except Exception as e:
        logger.warning("Failed to parse open_orders: %s", e)
        return []


def _parse_signal(data: dict[str, Any]) -> StrategySignalPreviewModel | None:
    try:
        return StrategySignalPreviewModel(
            signal_id=data.get("signal_id", "unknown"),
            symbol=data.get("symbol", "UNKNOWN"),
            feature_hash=data.get("feature_hash", ""),
            context_hash=data.get("context_hash", ""),
            policy_hash=data.get("policy_hash", ""),
            graph_trace_hash=data.get("graph_trace_hash", ""),
            confidence_score=_to_float(data.get("confidence_score")),
            direction=data.get("direction", "flat"),
            target_hint=_to_float(data.get("target_hint")) if data.get("target_hint") is not None else None,
            invalidation_hint=_to_float(data.get("invalidation_hint")) if data.get("invalidation_hint") is not None else None,
            size_hint=_to_float(data.get("size_hint")) if data.get("size_hint") is not None else None,
            preview_note=data.get("preview_note", "Preview only — NOT EXECUTABLE"),
            ts_event_ns=_to_int(data.get("ts_event_ns")),
            source_available=True,
            last_update_ts_ns=_to_int(data.get("ts_event_ns")),
            stale=False,
            missing=False,
            provenance="redis",
            source_status="live",
        )
    except Exception as e:
        logger.warning("Failed to parse signal: %s", e)
        return None


def _parse_gate(data: dict[str, Any]) -> GateDecisionModel | None:
    try:
        return GateDecisionModel(
            decision_id=data.get("decision_id", "unknown"),
            decision=data.get("decision", "HOLD"),
            first_blocking_gate=data.get("first_blocking_gate"),
            reason_code=data.get("reason_code", ""),
            confidence_delta=_to_float(data.get("confidence_delta")),
            size_modifier=_to_float(data.get("size_modifier")),
            target_hint=_to_float(data.get("target_hint")) if data.get("target_hint") is not None else None,
            invalidation_hint=_to_float(data.get("invalidation_hint")) if data.get("invalidation_hint") is not None else None,
            gate_decision_hash=data.get("gate_decision_hash", ""),
            source_signal_hash=data.get("source_signal_hash", ""),
            ts_event_ns=_to_int(data.get("ts_event_ns")),
            source_available=True,
            last_update_ts_ns=_to_int(data.get("ts_event_ns")),
            stale=False,
            missing=False,
            provenance="redis",
            source_status="live",
        )
    except Exception as e:
        logger.warning("Failed to parse gate: %s", e)
        return None


def _parse_trade_action(data: dict[str, Any]) -> TradeActionEvidenceModel | None:
    try:
        return TradeActionEvidenceModel(
            action_id=data.get("action_id", "unknown"),
            action=data.get("action", ""),
            side=data.get("side", "buy"),
            price=_to_float(data.get("price")),
            qty=_to_float(data.get("qty")),
            trade_action_hash=data.get("trade_action_hash", ""),
            source_gate_decision_hash=data.get("source_gate_decision_hash", ""),
            created_by=data.get("created_by", "run_gate_engine"),
            ts_event_ns=_to_int(data.get("ts_event_ns")),
            source_available=True,
            last_update_ts_ns=_to_int(data.get("ts_event_ns")),
            stale=False,
            missing=False,
            provenance="redis",
            source_status="live",
        )
    except Exception as e:
        logger.warning("Failed to parse trade_action: %s", e)
        return None


def _parse_execution(data: dict[str, Any]) -> ExecutionReportModel | None:
    try:
        return ExecutionReportModel(
            report_id=data.get("report_id", "unknown"),
            status=data.get("status", "SUBMITTED"),
            exchange_order_id=data.get("exchange_order_id"),
            client_order_id=data.get("client_order_id", "unknown"),
            trade_action_hash=data.get("trade_action_hash", ""),
            symbol=data.get("symbol", "UNKNOWN"),
            side=data.get("side", "buy"),
            filled_qty=_to_float(data.get("filled_qty", 0)),
            avg_fill_price=_to_float(data.get("avg_fill_price")) if data.get("avg_fill_price") is not None else None,
            submit_ts_ns=_to_int(data.get("submit_ts_ns")),
            ack_ts_ns=_to_int(data.get("ack_ts_ns")) if data.get("ack_ts_ns") else None,
            fill_ts_ns=_to_int(data.get("fill_ts_ns")) if data.get("fill_ts_ns") else None,
            submit_to_ack_us=_to_int(data.get("submit_to_ack_us")) if data.get("submit_to_ack_us") else None,
            ack_to_fill_us=_to_int(data.get("ack_to_fill_us")) if data.get("ack_to_fill_us") else None,
            rejection_reason=data.get("rejection_reason"),
            ts_event_ns=_to_int(data.get("ts_event_ns")),
            source_available=True,
            last_update_ts_ns=_to_int(data.get("ts_event_ns")),
            stale=False,
            missing=False,
            provenance="redis",
            source_status="live",
        )
    except Exception as e:
        logger.warning("Failed to parse execution: %s", e)
        return None


def _parse_quant_levels(data: dict[str, Any]) -> QuantLevelsContextModel | None:
    try:
        levels_raw = data.get("levels", [])
        levels = [
            QuantLevelModel(
                label=l.get("label", ""),
                price=_to_float(l.get("price")),
                kind=l.get("kind", "pivot"),
            )
            for l in levels_raw
        ]
        return QuantLevelsContextModel(
            symbol=data.get("symbol", "UNKNOWN"),
            levels=levels,
            ts_event_ns=_to_int(data.get("ts_event_ns")),
            source_available=True,
            last_update_ts_ns=_to_int(data.get("ts_event_ns")),
            stale=False,
            missing=False,
            provenance="redis",
            source_status="live",
        )
    except Exception as e:
        logger.warning("Failed to parse quant_levels: %s", e)
        return None


def _parse_tick_to_trade(data: dict[str, Any]) -> TickToTradeTraceModel | None:
    try:
        return TickToTradeTraceModel(
            trace_id=data.get("trace_id", "unknown"),
            tick_receive_ts_ns=_to_int(data.get("tick_receive_ts_ns")),
            signal_ts_ns=_to_int(data.get("signal_ts_ns")),
            gate_ts_ns=_to_int(data.get("gate_ts_ns")),
            execution_ts_ns=_to_int(data.get("execution_ts_ns")),
            tick_to_signal_us=_to_int(data.get("tick_to_signal_us")),
            signal_to_gate_us=_to_int(data.get("signal_to_gate_us")),
            gate_to_execution_us=_to_int(data.get("gate_to_execution_us")),
            total_tick_to_trade_us=_to_int(data.get("total_tick_to_trade_us")),
            ts_event_ns=_to_int(data.get("ts_event_ns")),
            source_available=True,
            last_update_ts_ns=_to_int(data.get("ts_event_ns")),
            stale=False,
            missing=False,
            provenance="redis",
            source_status="live",
        )
    except Exception as e:
        logger.warning("Failed to parse tick_to_trade: %s", e)
        return None


def _parse_runtime_health(data: dict[str, Any]) -> RuntimeHealthModel | None:
    try:
        def _lane(prefix: str) -> LaneHealthModel:
            return LaneHealthModel(
                lane=data.get(f"{prefix}_lane", prefix),
                status=data.get(f"{prefix}_status", "unknown"),
                last_heartbeat_ts_ns=_to_int(data.get(f"{prefix}_heartbeat_ns")) if data.get(f"{prefix}_heartbeat_ns") else None,
                age_ms=_to_int(data.get(f"{prefix}_age_ms")) if data.get(f"{prefix}_age_ms") else None,
                stale=bool(data.get(f"{prefix}_stale", False)),
                missing=bool(data.get(f"{prefix}_missing", False)),
                reason_code=data.get(f"{prefix}_reason"),
            )

        return RuntimeHealthModel(
            run_main_strategy_signal=_lane("main_strategy"),
            run_gate_engine=_lane("gate_engine"),
            run_execution_lane=_lane("execution_lane"),
            ai_lane_advisory=_lane("ai_advisory"),
            data_health=_lane("data"),
            ts_event_ns=_to_int(data.get("ts_event_ns")),
            source_available=True,
            last_update_ts_ns=_to_int(data.get("ts_event_ns")),
            stale=False,
            missing=False,
            provenance="redis",
            source_status="live",
        )
    except Exception as e:
        logger.warning("Failed to parse runtime_health: %s", e)
        return None


# Parser dispatch table — maps stream suffix → parser function.
_PARSERS = {
    "book_top": ("book_top", _parse_book_top),
    "book_l2": ("book_l2", _parse_book_l2),
    "account": ("account", _parse_account),
    "positions": ("positions", _parse_positions),
    "open_orders": ("open_orders", _parse_open_orders),
    "signal": ("latest_signal_preview", _parse_signal),
    "gate": ("latest_gate_decision", _parse_gate),
    "trade_action": ("latest_trade_action", _parse_trade_action),
    "execution": ("latest_execution_report", _parse_execution),
    "quant_levels": ("quant_levels", _parse_quant_levels),
    "tick_to_trade": ("tick_to_trade", _parse_tick_to_trade),
    "runtime_health": ("runtime_health", _parse_runtime_health),
}


def parse_stream_entry(stream_suffix: str, fields: dict[bytes, bytes]) -> tuple[str, Any] | None:
    """Parse a Redis stream entry into a (model_field, model) tuple.

    Returns None if the stream suffix is unknown or parsing fails.
    """
    if stream_suffix not in _PARSERS:
        logger.debug("Unknown stream suffix: %s", stream_suffix)
        return None
    field_name, parser = _PARSERS[stream_suffix]
    data = _parse_stream_entry(fields)
    result = parser(data)
    if result is None:
        return None
    return field_name, result


def build_snapshot_from_redis(entries: dict[str, dict[bytes, bytes]]) -> TradeHudSnapshot:
    """Build a TradeHudSnapshot from collected Redis stream entries.

    entries: dict mapping stream_suffix → latest stream entry fields.
    Missing streams result in None for that field (not zero).
    """
    snapshot_fields: dict[str, Any] = {}

    for suffix, fields in entries.items():
        parsed = parse_stream_entry(suffix, fields)
        if parsed:
            snapshot_fields[parsed[0]] = parsed[1]

    snapshot = TradeHudSnapshot(**snapshot_fields)
    snapshot.provenance = "redis"
    return snapshot


class RedisStreamAdapter:
    """Read-only Redis Stream consumer for ND runtime TradeHUD events.

    Uses XREAD to consume the latest entries from ND runtime streams.
    Never writes to Redis. Never exposes credentials. Falls back gracefully.

    Usage:
        adapter = RedisStreamAdapter()  # auto-connects if REDIS_URL set
        if adapter.is_connected():
            snapshot = await adapter.get_snapshot("BTCUSDT-PERP")
    """

    def __init__(self, redis_url: str | None = None) -> None:
        self._redis_url = redis_url or _get_redis_url()
        self._client = None
        self._last_ids: dict[str, str] = {}  # per-stream last consumed ID
        self._cached: dict[str, dict[bytes, bytes] | None] = {}  # latest cached entry per stream
        self._connected = False
        self._connect_error: str | None = None

        for key in _STREAM_KEYS:
            self._last_ids[key] = "$"  # start from latest on first read
            self._cached[key] = None

    async def connect(self) -> bool:
        """Attempt to connect to Redis. Returns True if connected."""
        if not self._redis_url:
            self._connected = False
            self._connect_error = "No REDIS_URL configured"
            return False

        try:
            import redis.asyncio as aioredis
            self._client = aioredis.from_url(
                self._redis_url,
                decode_responses=False,
                socket_connect_timeout=2,
                socket_timeout=2,
                retry_on_timeout=True,
            )
            # Ping to verify connection
            await self._client.ping()
            self._connected = True
            self._connect_error = None
            logger.info("RedisStreamAdapter connected to Redis")
            return True
        except ImportError:
            self._connected = False
            self._connect_error = "redis package not installed"
            logger.warning("redis package not installed — adapter disabled")
            return False
        except Exception as e:
            self._connected = False
            self._connect_error = str(e)
            logger.warning("Redis connection failed: %s — falling back to mock", e)
            self._client = None
            return False

    async def disconnect(self) -> None:
        """Close Redis connection cleanly."""
        if self._client:
            try:
                await self._client.aclose()
            except Exception:
                pass
            self._client = None
        self._connected = False

    def is_connected(self) -> bool:
        """Check if adapter is connected to Redis."""
        return self._connected and self._client is not None

    def is_configured(self) -> bool:
        """Check if Redis URL is configured (even if not connected)."""
        return self._redis_url is not None

    def get_connect_error(self) -> str | None:
        """Return last connection error if any."""
        return self._connect_error

    async def _read_stream(self, stream_suffix: str) -> dict[bytes, bytes] | None:
        """Read latest entry from a single stream via XREAD.

        Returns the entry fields dict, or None if no new data.
        """
        if not self.is_connected():
            return None

        stream_key = f"{_STREAM_PREFIX}{stream_suffix}"
        last_id = self._last_ids.get(stream_suffix, "$")

        try:
            result = await self._client.xread(
                {stream_key: last_id},
                count=_MAX_READ_COUNT,
                block=_XREAD_BLOCK_MS,
            )
        except Exception as e:
            logger.warning("XREAD failed for %s: %s", stream_key, e)
            return None

        if not result:
            return None  # no new data — caller uses cached value

        # result is [(stream_key, [(entry_id, {fields})])]
        for _stream, entries in result:
            for entry_id, fields in entries:
                self._last_ids[stream_suffix] = entry_id.decode() if isinstance(entry_id, bytes) else str(entry_id)
                self._cached[stream_suffix] = dict(fields)
                return dict(fields)

        return None

    async def _read_all_streams(self) -> dict[str, dict[bytes, bytes]]:
        """Read latest entries from all ND runtime streams.

        Returns dict mapping stream_suffix → entry fields (from cache or fresh read).
        Streams with no data are omitted from the result.
        """
        # Read all streams concurrently would be ideal, but we do sequential for simplicity
        # since XREAD BLOCK is short (500ms).
        fresh: dict[str, dict[bytes, bytes]] = {}

        for suffix in _STREAM_KEYS:
            entry = await self._read_stream(suffix)
            # Use fresh read if available, otherwise fall back to cached
            if entry:
                fresh[suffix] = entry
            elif self._cached.get(suffix):
                fresh[suffix] = self._cached[suffix]

        return fresh

    async def get_snapshot(self, symbol: str | None = None) -> TradeHudSnapshot | None:
        """Build a TradeHudSnapshot from latest Redis stream data.

        Returns None if no data is available from any stream.
        """
        entries = await self._read_all_streams()
        if not entries:
            return None
        return build_snapshot_from_redis(entries)

    async def get_health(self) -> dict[str, object]:
        """Return adapter health status for monitoring."""
        return {
            "status": "connected" if self.is_connected() else "disconnected",
            "redis_configured": self.is_configured(),
            "redis_connected": self.is_connected(),
            "has_runtime": self.is_connected(),
            "has_redis": self.is_connected(),
            "has_postgres": False,  # adapter never touches postgres
            "mode": "redis" if self.is_connected() else "mock",
            "provenance": "redis" if self.is_connected() else "mock",
            "error": self._connect_error,
            "streams": list(_STREAM_KEYS),
        }
