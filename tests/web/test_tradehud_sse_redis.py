"""Tests for SSE route with Redis adapter integration."""

import json
import os
import inspect
from unittest.mock import patch

import pytest

from services.api.routes.tradehud_sse import (
    tradehud_event_stream,
    tradehud_stream_response,
    _format_sse,
    _format_ping,
    _annotate,
    _scrub_credentials,
    _redis_configured,
    _try_redis_adapter,
)


def _parse_sse(raw):
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


def test_redis_configured_false_without_env():
    with patch.dict(os.environ, {}, clear=True):
        assert _redis_configured() is False


def test_redis_configured_true_with_url():
    with patch.dict(os.environ, {"REDIS_URL": "redis://localhost:6379"}):
        assert _redis_configured() is True


@pytest.mark.asyncio
async def test_try_redis_adapter_no_redis_url():
    with patch.dict(os.environ, {}, clear=True):
        adapter, connected = await _try_redis_adapter()
        assert adapter is None
        assert connected is False


@pytest.mark.asyncio
async def test_sse_falls_back_to_mock_without_redis():
    with patch.dict(os.environ, {}, clear=True):
        gen = tradehud_event_stream("BTCUSDT-PERP")
        first = await gen.__anext__()
        events = _parse_sse(first)
        assert events[0]["event"] == "snapshot"
        assert events[0]["data"]["provenance"] == "mock"
        assert events[0]["data"]["source_status"] == "synthetic"
        await gen.aclose()


@pytest.mark.asyncio
async def test_sse_falls_back_to_mock_on_connection_failure():
    """SSE stream falls back to mock when Redis connection fails."""
    with patch.dict(os.environ, {"REDIS_URL": "redis://unreachable:6379"}):
        gen = tradehud_event_stream("BTCUSDT-PERP")
        first = await gen.__anext__()
        events = _parse_sse(first)
        # Should still emit snapshot — just with mock provenance
        assert events[0]["event"] == "snapshot"
        assert events[0]["data"]["provenance"] == "mock"
        await gen.aclose()


@pytest.mark.asyncio
async def test_sse_ping_carries_current_provenance():
    with patch.dict(os.environ, {}, clear=True):
        gen = tradehud_event_stream("BTCUSDT-PERP")
        await gen.__anext__()
        await gen.aclose()
    ping_mock = _format_ping("mock", "synthetic")
    events = _parse_sse(ping_mock)
    assert events[0]["data"]["provenance"] == "mock"
    assert events[0]["data"]["source_status"] == "synthetic"


def test_scrub_credentials_strips_redis_url():
    payload = {
        "book_top": {"price": 50000},
        "redis_url": "redis://secret@host:6379",
        "api_key": "abc123",
        "database_url": "postgres://user@host/db",
    }
    scrubbed = _scrub_credentials(payload)
    assert "redis_url" not in scrubbed
    assert "database_url" not in scrubbed
    assert "api_key" not in scrubbed
    assert scrubbed["book_top"]["price"] == 50000


def test_sse_route_has_no_write_operations():
    src = inspect.getsource(__import__("services.api.routes.tradehud_sse", fromlist=[""]))
    forbidden = [".xadd(", ".set(", ".publish(", ".hset(", ".delete("]
    for pattern in forbidden:
        assert pattern not in src.lower(), f"Write op '{pattern}' in SSE route"


def test_sse_route_does_not_expose_redis_url_to_client():
    src = inspect.getsource(__import__("services.api.routes.tradehud_sse", fromlist=[""]))
    assert "NEXT_PUBLIC_REDIS_URL" not in src
    assert "NEXT_PUBLIC_DATABASE_URL" not in src


def test_stream_response_is_text_event_stream():
    resp = tradehud_stream_response("BTCUSDT-PERP")
    assert resp.media_type == "text/event-stream"
    assert "no-cache" in resp.headers.get("cache-control", "")
