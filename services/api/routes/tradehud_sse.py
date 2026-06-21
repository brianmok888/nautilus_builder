"""SSE event generator for TradeHUD — streams observational events.

Read-only. No order execution authority. No credentials.

Source selection (Phase 7):
- TRADEHUD_FEED_SOURCE=mock (default) → synthetic/mock SSE only
- TRADEHUD_FEED_SOURCE=redis → Redis adapter, fallback to mock if unavailable

Standard SSE framing — every message uses a named ``event:`` field.
"""

from __future__ import annotations

import json
import os
import logging
import time
from collections.abc import AsyncGenerator

import anyio
from fastapi.responses import StreamingResponse

from packages.tradehud_contracts.config import TradeHudRedisConfig
from packages.tradehud_contracts.service import TradeHudService

logger = logging.getLogger(__name__)

_SSE_PING_INTERVAL = 15.0
_SSE_EVENT_INTERVAL = 1.5
_LOOP_TICK = 0.2
_REDIS_RECONNECT_INTERVAL = 5.0
_STREAM_HEALTH_INTERVAL = 5.0

_SENSITIVE_SUFFIXES = frozenset(("_key", "_token", "_password", "_secret", "_url"))
_SENSITIVE_WORDS = frozenset(("apikey", "secret", "token", "password", "credential"))


def _is_sensitive_key(key: str) -> bool:
    kl = key.lower()
    return any(kl.endswith(suf) for suf in _SENSITIVE_SUFFIXES) or any(word in kl for word in _SENSITIVE_WORDS)


def _scrub_credentials(payload: dict) -> dict:
    cleaned = {}
    for key, value in payload.items():
        if _is_sensitive_key(key):
            continue
        cleaned[key] = value
    return cleaned



def _format_sse(event_type: str, data: dict) -> bytes:
    payload = json.dumps(data, default=str)
    return ("event: " + event_type + "\ndata: " + payload + "\n\n").encode()


def _format_ping(provenance: str = "mock", source_status: str = "synthetic") -> bytes:
    return _format_sse("ping", {
        "server_time": time.time(),
        "provenance": provenance,
        "source_status": source_status,
    })


def _annotate(payload: dict, provenance: str = "mock", source_status: str = "synthetic") -> dict:
    enriched = dict(payload)
    enriched["provenance"] = provenance
    enriched["source_status"] = source_status
    return _scrub_credentials(enriched)


def _model_dump(obj) -> object:
    if obj is None:
        return None
    return obj.model_dump(mode="json")


def _snapshot_to_event_payload(snapshot, provenance: str = "mock", source_status: str = "synthetic") -> dict:
    return _annotate(
        {
            "book_top": _model_dump(snapshot.book_top),
            "book_l2": _model_dump(snapshot.book_l2),
            "trades": [t.model_dump(mode="json") for t in snapshot.trades] if hasattr(snapshot, "trades") and snapshot.trades else [],
            "account": _model_dump(snapshot.account),
            "positions": [p.model_dump(mode="json") for p in snapshot.positions] if snapshot.positions else [],
            "quant_levels": _model_dump(snapshot.quant_levels),
            "runtime_health": _model_dump(snapshot.runtime_health),
            "latest_signal_preview": _model_dump(snapshot.latest_signal_preview),
            "latest_gate_decision": _model_dump(snapshot.latest_gate_decision),
            "latest_trade_action": _model_dump(snapshot.latest_trade_action),
            "latest_execution_report": _model_dump(snapshot.latest_execution_report),
        },
        provenance=provenance,
        source_status=source_status,
    )


def _is_redis_enabled() -> bool:
    """Redis adapter ONLY activates when TRADEHUD_FEED_SOURCE=redis."""
    config = TradeHudRedisConfig.from_env()
    return bool(config.is_redis_enabled and config.is_redis_configured)


def _is_production_env() -> bool:
    """True when the strictest configured Builder environment is production.

    In production, a configured-but-unavailable Redis feed must surface an explicit
    degraded signal rather than silently presenting a synthetic (alive-looking) stream.
    """
    raw = (os.environ.get("BUILDER_ENV", "") or os.environ.get("APP_ENV", "")).strip().lower()
    return raw == "production"


async def _try_redis_adapter():
    """Attempt to create and connect a RedisStreamAdapter.

    Returns (adapter, connected) tuple.
    """
    config = TradeHudRedisConfig.from_env()
    if not config.is_redis_enabled:
        return None, False
    if not config.is_redis_configured:
        return None, False
    try:
        from packages.tradehud_contracts.redis_adapter import RedisStreamAdapter
        adapter = RedisStreamAdapter(config)
        connected = await adapter.connect()
        if connected:
            logger.info("TradeHUD SSE using Redis adapter — provenance=redis, namespace=%s", config.stream_namespace)
            return adapter, True
        logger.info("Redis enabled but unreachable — falling back to mock")
        return None, False
    except ImportError:
        logger.info("redis package not installed — using mock")
        return None, False
    except Exception as e:
        logger.warning("Redis adapter init failed: %s — using mock", e)
        return None, False


async def tradehud_event_stream(
    symbol: str | None = None,
    service: TradeHudService | None = None,
) -> AsyncGenerator[bytes, None]:
    """Async generator yielding standard-framed SSE TradeHUD events."""
    sym = symbol or "BTCUSDT-PERP"
    mock_svc = service or TradeHudService(sym)
    tick = 0
    last_ping = time.monotonic()
    last_event = 0.0
    last_health_emit = 0.0

    redis_adapter, redis_connected = await _try_redis_adapter()
    use_redis = redis_connected and redis_adapter is not None
    provenance = "redis" if use_redis else "mock"
    source_status = "live" if use_redis else "synthetic"

    # P2-4: in production, a configured-but-unavailable Redis feed must surface an
    # explicit degraded signal rather than silently presenting a synthetic stream.
    if _is_redis_enabled() and not use_redis and _is_production_env():
        provenance = "none"
        source_status = "redis_unavailable"
        yield _format_sse(
            "stream_error",
            {
                "source_status": "redis_unavailable",
                "provenance": "none",
                "reason": "Redis feed configured but unavailable in production",
            },
        )

    # Initial snapshot
    snapshot = None
    if use_redis:
        snapshot = await redis_adapter.get_snapshot(sym)
    if snapshot is None:
        snapshot = mock_svc.get_snapshot(sym)
        provenance = "mock"
        source_status = "synthetic"
        use_redis = False

    snapshot_payload = dict(_snapshot_to_event_payload(snapshot, provenance, source_status))
    snapshot_payload["symbol"] = sym
    snapshot_payload["snapshot"] = True
    yield _format_sse("snapshot", snapshot_payload)

    last_redis_check = time.monotonic()

    try:
        while True:
            now = time.monotonic()

            # Periodic Redis reconnection check
            if not use_redis and _is_redis_enabled() and (now - last_redis_check) >= _REDIS_RECONNECT_INTERVAL:
                last_redis_check = now
                adapter, connected = await _try_redis_adapter()
                if connected and adapter is not None:
                    if redis_adapter:
                        await redis_adapter.disconnect()
                    redis_adapter = adapter
                    use_redis = True
                    provenance = "redis"
                    source_status = "live"

            # Periodic event emission
            if now - last_event >= _SSE_EVENT_INTERVAL:
                tick += 1
                last_event = now
                snap = None
                if use_redis and redis_adapter:
                    snap = await redis_adapter.get_snapshot(sym)
                    if snap is None:
                        snap = mock_svc.get_snapshot(sym)
                        provenance = "mock"
                        source_status = "synthetic"
                    else:
                        provenance = "redis"
                        source_status = "live"
                else:
                    snap = mock_svc.get_snapshot(sym)
                    provenance = "mock"
                    source_status = "synthetic"

                event_payload = _snapshot_to_event_payload(snap, provenance, source_status)
                event_payload["tick"] = tick
                event_payload["symbol"] = sym
                yield _format_sse("tradehud_event", event_payload)

            # Stream health event
            if use_redis and redis_adapter and (now - last_health_emit) >= _STREAM_HEALTH_INTERVAL:
                last_health_emit = now
                health = await redis_adapter.get_health()
                yield _format_sse("stream_health", _annotate(health, provenance, source_status))

            # Keep-alive ping
            if now - last_ping >= _SSE_PING_INTERVAL:
                last_ping = now
                yield _format_ping(provenance, source_status)

            await anyio.sleep(_LOOP_TICK)
    except (anyio.get_cancelled_exc_class(), GeneratorExit):
        if redis_adapter:
            await redis_adapter.disconnect()
        raise


def tradehud_stream_response(
    symbol: str | None = None,
    service: TradeHudService | None = None,
) -> StreamingResponse:
    return StreamingResponse(
        tradehud_event_stream(symbol, service),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
