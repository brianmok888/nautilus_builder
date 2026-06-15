"""SSE event generator for TradeHUD -- streams observational events.

Read-only. No order execution authority. No credentials.

Supports two data sources:
1. **Redis adapter** — reads live ND runtime events from Redis Streams.
   Activated when REDIS_URL is set and Redis is reachable.
2. **Mock/synthetic** — deterministic mock data (default, safe fallback).

Source selection is automatic:
  - If REDIS_URL configured AND Redis reachable → provenance="redis", source_status="live"
  - Otherwise → provenance="mock", source_status="synthetic" (fallback)

The SSE route NEVER exposes credentials. Redis URL stays server-side.
The browser never connects to Redis directly.

Standard SSE framing -- every message uses a named ``event:`` field::

    event: snapshot
    data: {"provenance": "mock", "source_status": "synthetic", ...}

    event: tradehud_event
    data: {"tick": 1, "provenance": "mock", "source_status": "synthetic", ...}

    event: ping
    data: {"server_time": 1.0, "provenance": "mock", "source_status": "synthetic"}
"""

from __future__ import annotations

import json
import logging
import os
import time
from collections.abc import AsyncGenerator

import anyio
from fastapi.responses import StreamingResponse

from packages.tradehud_contracts.service import TradeHudService

logger = logging.getLogger(__name__)

# SSE ping interval (seconds) -- keeps connection alive through proxies.
_SSE_PING_INTERVAL = 15.0
# Event emission interval (seconds).
_SSE_EVENT_INTERVAL = 1.5
# Poll cadence for the emit/ping decision loop (seconds).
_LOOP_TICK = 0.2
# Redis reconnection check interval (seconds).
_REDIS_RECONNECT_INTERVAL = 5.0

# Forbidden credential substrings -- defensively stripped from payloads.
_FORBIDDEN_CREDENTIAL_KEYS = (
    "api_key",
    "secret_key",
    "private_key",
    "token",
    "password",
    "redis_url",
    "postgres_url",
    "database_url",
)


def _scrub_credentials(payload: dict) -> dict:
    """Return a copy of *payload* with any credential-looking keys removed."""
    cleaned = {}
    for key, value in payload.items():
        key_l = key.lower()
        if any(bad in key_l for bad in _FORBIDDEN_CREDENTIAL_KEYS):
            continue
        cleaned[key] = value
    return cleaned


def _format_sse(event_type: str, data: dict) -> bytes:
    """Format a single SSE message using a named ``event:`` field."""
    payload = json.dumps(data, default=str)
    return ("event: " + event_type + "\ndata: " + payload + "\n\n").encode()


def _format_ping(provenance: str = "mock", source_status: str = "synthetic") -> bytes:
    """Keep-alive ping emitted as a named ``event: ping`` message."""
    return _format_sse("ping", {
        "server_time": time.time(),
        "provenance": provenance,
        "source_status": source_status,
    })


def _annotate(payload: dict, provenance: str = "mock", source_status: str = "synthetic") -> dict:
    """Attach provenance/source_status and scrub credentials from a payload."""
    enriched = dict(payload)
    enriched["provenance"] = provenance
    enriched["source_status"] = source_status
    return _scrub_credentials(enriched)


def _model_dump(obj) -> object:
    """Safely model_dump an optional pydantic model, else None."""
    if obj is None:
        return None
    return obj.model_dump(mode="json")


def _snapshot_to_event_payload(snapshot, provenance: str = "mock", source_status: str = "synthetic") -> dict:
    """Flatten a TradeHudSnapshot into the event payload dict."""
    return _annotate(
        {
            "book_top": _model_dump(snapshot.book_top),
            "book_l2": _model_dump(snapshot.book_l2),
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


def _redis_configured() -> bool:
    """Check if Redis URL is configured (server-side env only)."""
    return bool(os.environ.get("REDIS_URL") or os.environ.get("REDIS_CONNECTION_STRING"))


async def _try_redis_adapter():
    """Attempt to create and connect a RedisStreamAdapter.

    Returns (adapter, connected) tuple.
    If redis package not installed or connection fails, returns (None, False).
    """
    if not _redis_configured():
        return None, False
    try:
        from packages.tradehud_contracts.redis_adapter import RedisStreamAdapter
        adapter = RedisStreamAdapter()
        connected = await adapter.connect()
        if connected:
            logger.info("TradeHUD SSE using Redis adapter — provenance=redis")
            return adapter, True
        logger.info("Redis configured but unreachable — falling back to mock")
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
    """Async generator yielding standard-framed SSE TradeHUD events.

    Source selection:
    1. Try Redis adapter if REDIS_URL configured
    2. Fall back to mock TradeHudService if Redis unavailable

    Emits one event: snapshot on connect, then event: tradehud_event updates
    every 1.5s and an event: ping keep-alive every 15s.
    """
    sym = symbol or "BTCUSDT-PERP"
    mock_svc = service or TradeHudService(sym)
    tick = 0
    last_ping = time.monotonic()
    last_event = 0.0

    # Try Redis adapter
    redis_adapter, redis_connected = await _try_redis_adapter()
    use_redis = redis_connected and redis_adapter is not None

    provenance = "redis" if use_redis else "mock"
    source_status = "live" if use_redis else "synthetic"

    # Get initial snapshot
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

    # Track Redis reconnection
    last_redis_check = time.monotonic()

    try:
        while True:
            now = time.monotonic()

            # Periodically check if Redis came back (if we were using mock)
            if not use_redis and _redis_configured() and (now - last_redis_check) >= _REDIS_RECONNECT_INTERVAL:
                last_redis_check = now
                adapter, connected = await _try_redis_adapter()
                if connected and adapter is not None:
                    # Disconnect old adapter if any
                    if redis_adapter:
                        await redis_adapter.disconnect()
                    redis_adapter = adapter
                    use_redis = True
                    provenance = "redis"
                    source_status = "live"
                    logger.info("TradeHUD SSE switched to Redis adapter")

            if now - last_event >= _SSE_EVENT_INTERVAL:
                tick += 1
                last_event = now

                # Try to get latest data from active source
                snap = None
                if use_redis and redis_adapter:
                    snap = await redis_adapter.get_snapshot(sym)
                    if snap is None:
                        # Redis returned nothing — fall back to mock for this tick
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

            if now - last_ping >= _SSE_PING_INTERVAL:
                last_ping = now
                yield _format_ping(provenance, source_status)

            await anyio.sleep(_LOOP_TICK)
    except (anyio.get_cancelled_exc_class(), GeneratorExit):
        # Clean up Redis connection on disconnect
        if redis_adapter:
            await redis_adapter.disconnect()
        raise


def tradehud_stream_response(
    symbol: str | None = None,
    service: TradeHudService | None = None,
) -> StreamingResponse:
    """Build the GET /api/tradehud/stream StreamingResponse."""
    return StreamingResponse(
        tradehud_event_stream(symbol, service),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
