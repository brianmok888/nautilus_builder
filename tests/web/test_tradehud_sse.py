"""Tests for TradeHUD SSE event stream generator.

Verifies the SSE stream produces correctly formatted named events,
is read-only, and contains no credentials or order authority.
"""

import asyncio
import json
import inspect
from pathlib import Path

import pytest

from services.api.routes.tradehud_sse import (
    tradehud_event_stream,
    tradehud_stream_response,
    _format_sse,
    _format_ping,
    _annotate,
    _scrub_credentials,
)


def _parse_sse(raw: bytes) -> list[dict]:
    """Parse SSE bytes into list of {event, data} dicts."""
    events = []
    for block in raw.decode().split("\n\n"):
        block = block.strip()
        if not block:
            continue
        event_name = None
        data = None
        for line in block.split("\n"):
            if line.startswith("event:"):
                event_name = line.split(":", 1)[1].strip()
            elif line.startswith("data:"):
                data = json.loads(line.split(":", 1)[1].strip())
        if event_name:
            events.append({"event": event_name, "data": data})
    return events


@pytest.mark.asyncio
async def test_stream_returns_snapshot_first():
    """First event must be named 'snapshot' with provenance mock/synthetic."""
    gen = tradehud_event_stream("BTCUSDT-PERP")
    first = await gen.__anext__()
    events = _parse_sse(first)
    assert len(events) == 1
    assert events[0]["event"] == "snapshot"
    assert events[0]["data"]["provenance"] == "mock"
    assert events[0]["data"]["source_status"] == "synthetic"


@pytest.mark.asyncio
async def test_stream_emits_tradehud_events():
    """Stream should emit tradehud_event after snapshot."""
    gen = tradehud_event_stream("BTCUSDT-PERP")
    await gen.__anext__()  # skip snapshot
    # Advance time to trigger first event tick
    for _ in range(20):
        chunk = await gen.__anext__()
        events = _parse_sse(chunk)
        for ev in events:
            if ev["event"] == "tradehud_event":
                assert ev["data"]["provenance"] == "mock"
                assert ev["data"]["source_status"] == "synthetic"
                return
    pytest.fail("No tradehud_event emitted")


@pytest.mark.asyncio
async def test_stream_events_carry_provenance():
    """All events must carry provenance=mock and source_status=synthetic."""
    gen = tradehud_event_stream("BTCUSDT-PERP")
    for _ in range(3):
        chunk = await gen.__anext__()
        events = _parse_sse(chunk)
        for ev in events:
            assert ev["data"]["provenance"] == "mock"
            assert ev["data"]["source_status"] == "synthetic"


@pytest.mark.asyncio
async def test_ping_format():
    """Ping events must have server_time, provenance, source_status."""
    raw = _format_ping()
    events = _parse_sse(raw)
    assert len(events) == 1
    assert events[0]["event"] == "ping"
    assert "server_time" in events[0]["data"]
    assert events[0]["data"]["provenance"] == "mock"
    assert events[0]["data"]["source_status"] == "synthetic"


@pytest.mark.asyncio
async def test_snapshot_has_book_data():
    """Snapshot must include book_top, book_l2, account."""
    gen = tradehud_event_stream("BTCUSDT-PERP")
    first = await gen.__anext__()
    events = _parse_sse(first)
    data = events[0]["data"]
    assert "book_top" in data
    assert "book_l2" in data
    assert "account" in data


def test_stream_response_is_text_event_stream():
    """tradehud_stream_response returns StreamingResponse with correct media type."""
    resp = tradehud_stream_response("BTCUSDT-PERP")
    assert resp.media_type == "text/event-stream"
    assert "no-cache" in resp.headers.get("cache-control", "")


def test_format_sse_uses_named_events():
    """SSE messages must use 'event:' field for named events."""
    raw = _format_sse("tradehud_event", {"test": True})
    text = raw.decode()
    assert "event: tradehud_event" in text
    assert "data:" in text


def test_scrub_credentials():
    """Credential keys must be stripped from payloads."""
    payload = {
        "api_key": "secret",
        "secret_key": "hidden",
        "normal_field": "safe",
        "token": "bearer",
        "redis_url": "redis://...",
        "book_top": {"bid_price": 100},
    }
    cleaned = _scrub_credentials(payload)
    assert "api_key" not in cleaned
    assert "secret_key" not in cleaned
    assert "token" not in cleaned
    assert "redis_url" not in cleaned
    assert "normal_field" in cleaned
    assert "book_top" in cleaned


def test_no_post_routes_in_module():
    """Module must not expose POST/submit/cancel/modify/approve functions."""
    src = inspect.getsource(__import__("services.api.routes.tradehud_sse", fromlist=[""]))
    forbidden = ["@app.post", "def submit", "def cancel", "def modify", "def approve", "def force"]
    for pattern in forbidden:
        assert pattern not in src.lower(), f"Forbidden pattern '{pattern}' found in tradehud_sse.py"


def test_no_credentials_in_module():
    """Module source must not contain hardcoded credentials."""
    src = inspect.getsource(__import__("services.api.routes.tradehud_sse", fromlist=[""]))
    forbidden = [
        "BINANCE_SECRET", "BYBIT_SECRET", "OKX_SECRET", "DERIBIT_SECRET",
        "POLYMARKET_PRIVATE_KEY", "NEXT_PUBLIC_REDIS_URL", "NEXT_PUBLIC_DATABASE_URL",
    ]
    for pattern in forbidden:
        assert pattern not in src, f"Forbidden credential pattern '{pattern}' in tradehud_sse.py"


def test_demo_server_is_local_only():
    """sse_demo_server.py must have LOCAL DEVELOPMENT ONLY warning."""
    demo_path = Path(__file__).parent.parent.parent / "services" / "api" / "sse_demo_server.py"
    if not demo_path.exists():
        demo_path = Path(__file__).parent.parent.parent / "sse_demo_server.py"
    content = demo_path.read_text()
    assert "LOCAL DEVELOPMENT ONLY" in content, "sse_demo_server.py missing local-only warning"
    assert "Do not use this as production" in content


def test_production_app_does_not_import_demo_server():
    """fastapi_app.py must not import sse_demo_server."""
    import services.api.fastapi_app as fa
    src = inspect.getsource(fa)
    assert "sse_demo_server" not in src, "Production app imports demo server!"
