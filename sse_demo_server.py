"""Standalone TradeHUD SSE server — no heavy deps needed.
Serves snapshot, health, and SSE stream endpoints.
"""
import asyncio
import json
import time
import sys
import os

sys.path.insert(0, os.getcwd())

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from packages.tradehud_contracts.service import TradeHudService

app = FastAPI(title="TradeHUD SSE Demo")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_SSE_PING = 15.0
_SSE_EVENT = 1.5


def _sse(event_type: str, data: dict) -> bytes:
    payload = json.dumps({"type": event_type, "payload": data}, default=str)
    return f"data: {payload}\n\n".encode()


@app.get("/api/tradehud/snapshot")
def snapshot(symbol: str | None = None):
    svc = TradeHudService(symbol or "BTCUSDT-PERP")
    return svc.get_snapshot(symbol).model_dump(mode="json")


@app.get("/api/tradehud/health")
def health():
    return {
        "status": "ok",
        "mode": "mock",
        "provenance": "mock",
        "has_runtime": False,
        "has_redis": False,
        "has_postgres": False,
        "message": "TradeHUD SSE demo — observational only",
    }


@app.get("/api/tradehud/stream")
async def stream(symbol: str | None = None):
    sym = symbol or "BTCUSDT-PERP"
    svc = TradeHudService(sym)
    tick = 0
    last_ping = time.monotonic()
    last_event = 0.0

    # Initial snapshot burst
    snap = svc.get_snapshot(sym)
    initial_events: list[bytes] = []
    if snap.book_top:
        initial_events.append(_sse("BOOK_TOP", snap.book_top.model_dump(mode="json")))
    if snap.book_l2:
        initial_events.append(_sse("BOOK_L2", snap.book_l2.model_dump(mode="json")))
    if snap.account:
        initial_events.append(_sse("ACCOUNT", snap.account.model_dump(mode="json")))
    if snap.positions:
        initial_events.append(_sse("POSITIONS", snap.positions))
    if snap.quant_levels:
        initial_events.append(_sse("QUANT_LEVELS", snap.quant_levels.model_dump(mode="json")))
    if snap.runtime_health:
        initial_events.append(_sse("RUNTIME_HEALTH", snap.runtime_health.model_dump(mode="json")))
    for ev in initial_events:
        yield ev

    while True:
        now = time.monotonic()
        if now - last_event >= _SSE_EVENT:
            tick += 1
            last_event = now
            snap = svc.get_snapshot(sym)
            yield _sse("BOOK_TOP", snap.book_top.model_dump(mode="json"))
            if snap.book_l2:
                yield _sse("BOOK_L2", snap.book_l2.model_dump(mode="json"))
            if snap.account:
                yield _sse("ACCOUNT", snap.account.model_dump(mode="json"))
            if snap.quant_levels:
                yield _sse("QUANT_LEVELS", snap.quant_levels.model_dump(mode="json"))
            if snap.runtime_health:
                yield _sse("RUNTIME_HEALTH", snap.runtime_health.model_dump(mode="json"))
            if tick % 10 == 0 and snap.latest_signal_preview:
                yield _sse("SIGNAL_PREVIEW", snap.latest_signal_preview.model_dump(mode="json"))
            if tick % 10 == 0 and snap.latest_gate_decision:
                yield _sse("GATE_DECISION", snap.latest_gate_decision.model_dump(mode="json"))

        if now - last_ping >= _SSE_PING:
            last_ping = now
            yield b": ping\n\n"

        await asyncio.sleep(0.2)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
