"""SSE event generator for TradeHUD -- streams observational events.

Read-only. No order execution authority. No credentials.
Streams mock/synthetic events by default.

Standard SSE framing -- every message uses a named ``event:`` field so that
EventSource clients dispatch via addEventListener('snapshot' |
'tradehud_event' | 'ping') instead of parsing every data frame:

    event: snapshot
    data: {"provenance": "mock", "source_status": "synthetic", ...}

    event: tradehud_event
    data: {"tick": 1, "provenance": "mock", "source_status": "synthetic", ...}

    event: ping
    data: {"server_time": 1.0, "provenance": "mock", "source_status": "synthetic"}

Disconnect safety -- the generator is cooperative with cancellation: when
Starlette cancels the streaming task (client disconnect) anyio raises a
cancellation that unwinds the generator via its except path. No background
tasks are spawned, so there is nothing to leak.
"""

from __future__ import annotations

import json
import time
from collections.abc import AsyncGenerator

import anyio
from fastapi.responses import StreamingResponse

from packages.tradehud_contracts.service import TradeHudService

# SSE ping interval (seconds) -- keeps connection alive through proxies.
_SSE_PING_INTERVAL = 15.0
# Event emission interval (seconds).
_SSE_EVENT_INTERVAL = 1.5
# Poll cadence for the emit/ping decision loop (seconds).
_LOOP_TICK = 0.2

# Provenance markers injected into every event so consumers always know the
# data is mock/synthetic and never a live runtime source.
_PROVENANCE = "mock"
_SOURCE_STATUS = "synthetic"

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
    """Return a copy of *payload* with any credential-looking keys removed.

    Mock data sources never emit these fields, but we strip them regardless
    so a future real source cannot accidentally leak secrets into the
    read-only stream.
    """
    cleaned = {}
    for key, value in payload.items():
        key_l = key.lower()
        if any(bad in key_l for bad in _FORBIDDEN_CREDENTIAL_KEYS):
            continue
        cleaned[key] = value
    return cleaned


def _format_sse(event_type: str, data: dict) -> bytes:
    """Format a single SSE message using a named ``event:`` field.

    Produces standard framing::

        event: <event_type>
        data: <json>

        <blank line>
    """
    payload = json.dumps(data, default=str)
    return ("event: " + event_type + "\ndata: " + payload + "\n\n").encode()


def _format_ping() -> bytes:
    """Keep-alive ping emitted as a named ``event: ping`` message."""
    return _format_sse(
        "ping",
        {
            "server_time": time.time(),
            "provenance": _PROVENANCE,
            "source_status": _SOURCE_STATUS,
        },
    )


def _annotate(payload: dict) -> dict:
    """Attach provenance/source_status and scrub credentials from a payload."""
    enriched = dict(payload)
    enriched["provenance"] = _PROVENANCE
    enriched["source_status"] = _SOURCE_STATUS
    return _scrub_credentials(enriched)


def _model_dump(obj) -> object:
    """Safely model_dump an optional pydantic model, else None."""
    if obj is None:
        return None
    return obj.model_dump(mode="json")


def _snapshot_to_event_payload(snapshot) -> dict:
    """Flatten a TradeHudSnapshot into the event payload dict."""
    return _annotate(
        {
            "book_top": _model_dump(snapshot.book_top),
            "book_l2": _model_dump(snapshot.book_l2),
            "account": _model_dump(snapshot.account),
            "positions": snapshot.positions,
            "quant_levels": _model_dump(snapshot.quant_levels),
            "runtime_health": _model_dump(snapshot.runtime_health),
            "latest_signal_preview": _model_dump(snapshot.latest_signal_preview),
            "latest_gate_decision": _model_dump(snapshot.latest_gate_decision),
            "latest_trade_action": _model_dump(snapshot.latest_trade_action),
            "latest_execution_report": _model_dump(snapshot.latest_execution_report),
        }
    )


async def tradehud_event_stream(
    symbol: str | None = None,
    service: TradeHudService | None = None,
) -> AsyncGenerator[bytes, None]:
    """Async generator yielding standard-framed SSE TradeHUD events.

    Emits one event: snapshot on connect, then event: tradehud_event updates
    every 1.5s and an event: ping keep-alive every 15s.

    Safe to cancel -- anyio cancellation unwinds this generator through its
    except path on client disconnect. No background tasks are created.
    """
    sym = symbol or "BTCUSDT-PERP"
    svc = service or TradeHudService(sym)
    tick = 0
    last_ping = time.monotonic()
    last_event = 0.0

    snapshot = svc.get_snapshot(sym)
    snapshot_payload = dict(_snapshot_to_event_payload(snapshot))
    snapshot_payload["symbol"] = sym
    snapshot_payload["snapshot"] = True
    yield _format_sse("snapshot", snapshot_payload)

    try:
        while True:
            now = time.monotonic()
            if now - last_event >= _SSE_EVENT_INTERVAL:
                tick += 1
                last_event = now
                snap = svc.get_snapshot(sym)
                event_payload = _snapshot_to_event_payload(snap)
                event_payload["tick"] = tick
                event_payload["symbol"] = sym
                yield _format_sse("tradehud_event", event_payload)
            if now - last_ping >= _SSE_PING_INTERVAL:
                last_ping = now
                yield _format_ping()
            await anyio.sleep(_LOOP_TICK)
    except (anyio.get_cancelled_exc_class(), GeneratorExit):
        raise


def tradehud_stream_response(
    symbol: str | None = None,
    service: TradeHudService | None = None,
) -> StreamingResponse:
    """Build the GET /api/tradehud/stream StreamingResponse.

    Returns a text/event-stream response backed by tradehud_event_stream.
    Disables proxy buffering so named events flush immediately. Cancellation
    from a client disconnect propagates into the generator's cancellation path.
    """
    return StreamingResponse(
        tradehud_event_stream(symbol, service),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
