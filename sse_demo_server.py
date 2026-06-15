"""LOCAL DEVELOPMENT ONLY.

This demo server exists to preview the TradeHUD SSE stream without running
full Builder API. It intentionally uses permissive local CORS for development.

Do not use this as production service.
Do not reference it from production Dockerfiles, deployment scripts, or systemd units.
It does not provide authentication, authorization, live runtime integration,
or exchange/order authority.
"""
import asyncio
import json
import logging
import time
import sys
import os

sys.path.insert(0, os.getcwd())

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from packages.tradehud_contracts.service import TradeHudService

logger = logging.getLogger("tradehud_sse_demo")

app = FastAPI(title="TradeHUD SSE Demo — LOCAL DEV ONLY")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_SSE_PING = 15.0
_SSE_EVENT = 1.5
_PROVENANCE = "mock"
_SOURCE_STATUS = "synthetic"


def _sse(event_type: str, data: dict) -> bytes:
    payload = json.dumps(data, default=str)
    return (f"event: {event_type}\ndata: {payload}\n\n").encode()


def _annotate(payload: dict) -> dict:
    payload["provenance"] = _PROVENANCE
    payload["source_status"] = _SOURCE_STATUS
    return payload


def _model_dump(obj) -> object:
    if obj is None:
        return None
    return obj.model_dump(mode="json")


@app.get("/api/tradehud/snapshot")
def snapshot(symbol: str | None = None):
    svc = TradeHudService(symbol or "BTCUSDT-PERP")
    snap = svc.get_snapshot(symbol)
    return _annotate(snap.model_dump(mode="json"))


@app.get("/api/tradehud/health")
def health():
    return {
        "status": "ok",
        "mode": "mock",
        "provenance": _PROVENANCE,
        "source_status": _SOURCE_STATUS,
        "has_runtime": False,
        "has_redis": False,
        "has_postgres": False,
        "message": "TradeHUD SSE demo — LOCAL DEVELOPMENT ONLY — observational",
    }


@app.get("/api/tradehud/stream")
async def stream(symbol: str | None = None):
    """SSE stream using standard named-event framing."""
    sym = symbol or "BTCUSDT-PERP"
    svc = TradeHudService(sym)
    tick = 0
    last_ping = time.monotonic()
    last_event = 0.0

    async def gen():
        nonlocal tick, last_ping, last_event
        # Initial snapshot burst as named event
        snap = svc.get_snapshot(sym)
        payload = _annotate({
            "book_top": _model_dump(snap.book_top),
            "book_l2": _model_dump(snap.book_l2),
            "account": _model_dump(snap.account),
            "positions": snap.positions,
            "quant_levels": _model_dump(snap.quant_levels),
            "runtime_health": _model_dump(snap.runtime_health),
            "symbol": sym,
            "snapshot": True,
        })
        yield _sse("snapshot", payload)

        while True:
            now = time.monotonic()
            if now - last_event >= _SSE_EVENT:
                tick += 1
                last_event = now
                snap = svc.get_snapshot(sym)
                ev = _annotate({
                    "book_top": _model_dump(snap.book_top),
                    "book_l2": _model_dump(snap.book_l2),
                    "account": _model_dump(snap.account),
                    "positions": snap.positions,
                    "quant_levels": _model_dump(snap.quant_levels),
                    "runtime_health": _model_dump(snap.runtime_health),
                    "tick": tick,
                    "symbol": sym,
                })
                if tick % 10 == 0 and snap.latest_signal_preview:
                    ev["signal_preview"] = _model_dump(snap.latest_signal_preview)
                if tick % 10 == 0 and snap.latest_gate_decision:
                    ev["gate_decision"] = _model_dump(snap.latest_gate_decision)
                yield _sse("tradehud_event", ev)
            if now - last_ping >= _SSE_PING:
                last_ping = now
                yield _sse("ping", {
                    "server_time": time.time(),
                    "provenance": _PROVENANCE,
                    "source_status": _SOURCE_STATUS,
                })
            await asyncio.sleep(0.2)

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )


if __name__ == "__main__":
    import uvicorn
    logger.warning("=" * 60)
    logger.warning("TradeHUD SSE demo server is LOCAL DEVELOPMENT ONLY.")
    logger.warning("Do NOT use in production. No auth. No live runtime.")
    logger.warning("=" * 60)
    logging.basicConfig(level=logging.INFO)
    uvicorn.run(app, host="0.0.0.0", port=8000)
