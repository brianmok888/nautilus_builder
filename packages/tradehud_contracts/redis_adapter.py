"""TradeHUD Redis stream adapter — connection, IO, and snapshot assembly.

Concerns are split across three modules (behavior unchanged; extracted from the
original monolith):
- `redis_normalizers`: the `_parse_*` parsers, `_PARSERS` dispatch table, and
  `parse_stream_entry`.
- `redis_snapshot_builder`: `build_snapshot_from_redis`.
- `redis_adapter` (this module): `RedisStreamAdapter` (Redis connection, XREAD/XADD
  IO, caching, health) plus backward-compatible re-exports of the public parse/
  snapshot symbols.

Public API preserved for backward compatibility:
    RedisStreamAdapter, parse_stream_entry, build_snapshot_from_redis
"""

from __future__ import annotations

import logging
from typing import Any

from packages.tradehud_contracts.config import TradeHudRedisConfig
from packages.tradehud_contracts.normalizer import parse_stream_fields, to_optional_int
from packages.tradehud_contracts.stream_health import StreamHealthTracker
from packages.tradehud_contracts.models import MarketTradeModel, TradeHudSnapshot

# Re-exported for backward compatibility. Tests and other callers historically
# imported the parse/snapshot helpers (including the internal `_parse_*`
# functions) directly from redis_adapter; the split must not break them.
from packages.tradehud_contracts.redis_normalizers import (  # noqa: F401
    _PARSERS,
    _ns,
    _parse_account,
    _parse_book_l2,
    _parse_book_top,
    _parse_execution,
    _parse_gate,
    _parse_open_orders,
    _parse_positions,
    _parse_quant_levels,
    _parse_runtime_health,
    _parse_signal,
    _parse_tick_to_trade,
    _parse_trade,
    _parse_trade_action,
    parse_stream_entry,
)
from packages.tradehud_contracts.redis_snapshot_builder import (  # noqa: F401
    build_snapshot_from_redis,
)

logger = logging.getLogger(__name__)


def _build_reverse_map(config: TradeHudRedisConfig) -> dict[str, str]:
    return {v: k for k, v in config.get_stream_map().items()}


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
