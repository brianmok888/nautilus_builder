"""SSE event generator for TradeHUD — streams observational events.

Read-only. No order execution authority. No credentials.
Streams mock/synthetic events by default. When a real runtime source
(Redis stream, Nautilus-Daedalus) becomes available, the generator
will read from that source instead — but still observational only.
"""

from __future__ import annotations

import asyncio
import json
import time
from collections.abc import AsyncGenerator
from packages.tradehud_contracts.service import TradeHudService

# SSE ping interval (seconds) — keeps connection alive through proxies
_SSE_PING_INTERVAL = 15.0
# Event emission interval (seconds)
_SSE_EVENT_INTERVAL = 1.5


def _format_sse(event_type: str, data: dict) -> bytes:
    """Format a single SSE message."""
    payload = json.dumps({"type": event_type, "payload": data}, default=str)
    return f"data: {payload}\n\n".encode()


def _format_ping() -> bytes:
    """Keep-alive ping."""
    return b": ping\n\n"


async def tradehud_event_stream(
    symbol: str | None = None,
    service: TradeHudService | None = None,
) -> AsyncGenerator[bytes, None]:
    """Async generator yielding SSE-formatted TradeHUD events.

    Yields mock/synthetic observational data at fixed intervals.
    Safe to cancel — generator cleans up on disconnect.

    Parameters
    ----------
    symbol : str | None
        Trading symbol to stream data for.
    service : TradeHudService | None
        Inject service for testing. Creates default if None.

    Yields
    ------
    bytes
        SSE-formatted message chunks.
    """
    svc = service or TradeHudService(symbol or "BTCUSDT-PERP")
    sym = symbol or "BTCUSDT-PERP"
    tick = 0
    last_ping = time.monotonic()
    last_event = 0.0

    # Send initial snapshot as a burst of events
    snapshot = svc.get_snapshot(sym)
    if snapshot.book_top:
        yield _format_sse("BOOK_TOP", snapshot.book_top.model_dump(mode="json"))
    if snapshot.book_l2:
        yield _format_sse("BOOK_L2", snapshot.book_l2.model_dump(mode="json"))
    if snapshot.account:
        yield _format_sse("ACCOUNT", snapshot.account.model_dump(mode="json"))
    if snapshot.positions:
        yield _format_sse("POSITIONS", snapshot.positions)
    if snapshot.quant_levels:
        yield _format_sse("QUANT_LEVELS", snapshot.quant_levels.model_dump(mode="json"))
    if snapshot.runtime_health:
        yield _format_sse("RUNTIME_HEALTH", snapshot.runtime_health.model_dump(mode="json"))

    # Stream updates
    while True:
        now = time.monotonic()

        # Emit events at fixed interval
        if now - last_event >= _SSE_EVENT_INTERVAL:
            tick += 1
            last_event = now
            snapshot = svc.get_snapshot(sym)

            yield _format_sse("BOOK_TOP", snapshot.book_top.model_dump(mode="json"))
            if snapshot.book_l2:
                yield _format_sse("BOOK_L2", snapshot.book_l2.model_dump(mode="json"))
            if snapshot.account:
                yield _format_sse("ACCOUNT", snapshot.account.model_dump(mode="json"))
            if snapshot.quant_levels:
                yield _format_sse("QUANT_LEVELS", snapshot.quant_levels.model_dump(mode="json"))
            if snapshot.runtime_health:
                yield _format_sse("RUNTIME_HEALTH", snapshot.runtime_health.model_dump(mode="json"))

            # Periodically emit evidence events (every ~10 ticks)
            if tick % 10 == 0 and snapshot.latest_signal_preview:
                yield _format_sse("SIGNAL_PREVIEW", snapshot.latest_signal_preview.model_dump(mode="json"))
            if tick % 10 == 0 and snapshot.latest_gate_decision:
                yield _format_sse("GATE_DECISION", snapshot.latest_gate_decision.model_dump(mode="json"))

        # Keep-alive ping
        if now - last_ping >= _SSE_PING_INTERVAL:
            last_ping = now
            yield _format_ping()

        # Yield control to event loop
        await asyncio.sleep(0.2)
