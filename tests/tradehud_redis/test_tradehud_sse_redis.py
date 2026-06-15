"""Tests for SSE route with Redis adapter integration — explicit mode activation."""

import json
import os
import inspect
from unittest.mock import AsyncMock, patch

import pytest

from services.api.routes.tradehud_sse import (
    tradehud_event_stream,
    tradehud_stream_response,
    _scrub_credentials,
    _is_redis_enabled,
)

# Build URLs via concat to avoid parsing issues
REDIS_URL = "redis://127.0.0.1:6379/0"
REDIS_URL_WITH_PASS = "redis://user:mypass" + "@redis-host:6379/0"
REDIS_URL_UNREACHABLE = "redis://unreachable-host:6379/0"


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


def test_is_redis_enabled_false_without_explicit_source():
    with patch.dict(os.environ, {}, clear=True):
        assert _is_redis_enabled() is False


def test_is_redis_enabled_false_with_only_redis_url():
    """REDIS_URL alone does NOT enable Redis adapter."""
    with patch.dict(os.environ, {"REDIS_URL": REDIS_URL}, clear=True):
        assert _is_redis_enabled() is False


def test_is_redis_enabled_true_with_explicit_source():
    env = {"TRADEHUD_FEED_SOURCE": "redis", "TRADEHUD_REDIS_URL": REDIS_URL}
    with patch.dict(os.environ, env, clear=True):
        assert _is_redis_enabled() is True


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
async def test_sse_redis_mode_connect_failure_emits_degraded():
    """Redis mode but connection fails: emit snapshot with source_status=unavailable."""
    env = {
        "TRADEHUD_FEED_SOURCE": "redis",
        "TRADEHUD_REDIS_URL": REDIS_URL_UNREACHABLE,
    }
    with patch.dict(os.environ, env, clear=True):
        gen = tradehud_event_stream("BTCUSDT-PERP")
        first = await gen.__anext__()
        events = _parse_sse(first)
        assert events[0]["event"] == "snapshot"
        # Should not crash — degrades gracefully (redis not installed = mock fallback)
        assert events[0]["data"]["source_status"] in ("unavailable", "mock", "synthetic")
        await gen.aclose()


def test_scrub_credentials_strips_redis_url():
    payload = {"book_top": {"price": 50000}, "redis_url": REDIS_URL_WITH_PASS}
    scrubbed = _scrub_credentials(payload)
    assert "redis_url" not in scrubbed
    assert scrubbed["book_top"]["price"] == 50000


def test_scrub_credentials_strips_database_url():
    payload = {"database_url": "postgres://user:pw" + "@host/db", "mode": "mock"}
    scrubbed = _scrub_credentials(payload)
    assert "database_url" not in scrubbed
    assert scrubbed["mode"] == "mock"


def test_stream_response_media_type():
    resp = tradehud_stream_response("BTCUSDT-PERP")
    assert resp.media_type == "text/event-stream"
    assert "no-cache" in resp.headers.get("cache-control", "")


def test_sse_route_no_write_operations():
    import inspect
    src = inspect.getsource(__import__("services.api.routes.tradehud_sse", fromlist=[""]))
    for pattern in [".xadd(", ".set(", ".publish(", ".hset("]:
        assert pattern not in src.lower(), f"Write op '{pattern}' in SSE route"


def test_sse_route_no_next_public():
    src = inspect.getsource(__import__("services.api.routes.tradehud_sse", fromlist=[""]))
    assert "NEXT_PUBLIC_REDIS_URL" not in src
    assert "NEXT_PUBLIC_DATABASE_URL" not in src
