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


@pytest.mark.asyncio
async def test_sse_production_redis_unavailable_emits_stream_error_then_stops():
    """P2-4 (tightened): in production, a configured-but-unavailable Redis feed must
    emit an explicit stream_error event and then STOP the generator. It must NOT
    continue into a synthetic/mock snapshot that makes a broken live feed look
    alive. Local/dev may still fall back to mock."""
    env = {
        "TRADEHUD_FEED_SOURCE": "redis",
        "TRADEHUD_REDIS_URL": REDIS_URL_UNREACHABLE,
        "BUILDER_ENV": "production",
    }
    with patch.dict(os.environ, env, clear=True):
        gen = tradehud_event_stream("BTCUSDT-PERP")
        seen_events = []
        try:
            # The very first event must be the explicit stream_error.
            first = _parse_sse(await gen.__anext__())
            seen_events.extend(first if isinstance(first, list) else [first])
            # After the stream_error the generator must terminate; the next pull
            # must raise StopAsyncIteration (no synthetic snapshot may follow).
            stopped = False
            try:
                await gen.__anext__()
            except StopAsyncIteration:
                stopped = True
            assert stopped, (
                "Production Redis-unavailable stream continued past stream_error "
                "instead of stopping the generator"
            )
        finally:
            await gen.aclose()

    event_names = {e["event"] for e in seen_events}
    source_statuses = {
        e["data"].get("source_status")
        for e in seen_events
        if isinstance(e.get("data"), dict)
    }
    # Production must surface the explicit degraded signal as the first event.
    assert "stream_error" in event_names
    assert "redis_unavailable" in source_statuses
    # No synthetic/mock (alive-looking) snapshot may be emitted after the error.
    assert "synthetic" not in source_statuses
    assert "mock" not in {e["data"].get("provenance") for e in seen_events if isinstance(e.get("data"), dict)}


@pytest.mark.asyncio
async def test_sse_staging_redis_unavailable_emits_stream_error_then_stops():
    """P2-4 (staging parity): in staging, a configured-but-unavailable Redis feed
    must emit stream_error and stop the generator, just like production. Staging is
    a non-local environment where a broken live feed must not be masked by a
    synthetic (alive-looking) snapshot. Only local/dev falls back to mock."""
    env = {
        "TRADEHUD_FEED_SOURCE": "redis",
        "TRADEHUD_REDIS_URL": REDIS_URL_UNREACHABLE,
        "BUILDER_ENV": "staging",
    }
    with patch.dict(os.environ, env, clear=True):
        gen = tradehud_event_stream("BTCUSDT-PERP")
        seen_events = []
        try:
            first = _parse_sse(await gen.__anext__())
            seen_events.extend(first if isinstance(first, list) else [first])
            stopped = False
            try:
                await gen.__anext__()
            except StopAsyncIteration:
                stopped = True
            assert stopped, (
                "Staging Redis-unavailable stream continued past stream_error "
                "instead of stopping the generator"
            )
        finally:
            await gen.aclose()

    event_names = {e["event"] for e in seen_events}
    source_statuses = {
        e["data"].get("source_status")
        for e in seen_events
        if isinstance(e.get("data"), dict)
    }
    assert "stream_error" in event_names
    assert "redis_unavailable" in source_statuses
    # No synthetic/mock snapshot may follow in staging.
    assert "synthetic" not in source_statuses


@pytest.mark.asyncio
async def test_sse_local_dev_redis_unavailable_still_falls_back_to_mock():
    """P2-4 (complement): local/dev with Redis configured-but-unavailable must
    keep the existing fallback to a synthetic/mock snapshot (unchanged behavior)."""
    env = {
        "TRADEHUD_FEED_SOURCE": "redis",
        "TRADEHUD_REDIS_URL": REDIS_URL_UNREACHABLE,
        "BUILDER_ENV": "local",
    }
    with patch.dict(os.environ, env, clear=True):
        gen = tradehud_event_stream("BTCUSDT-PERP")
        seen_events = []
        try:
            for _ in range(2):
                seen_events.append(_parse_sse(await gen.__anext__()))
        except StopAsyncIteration:
            pass
        finally:
            await gen.aclose()

    flat = [e for batch in seen_events for e in batch]
    event_names = {e["event"] for e in flat}
    # Local/dev must NOT emit a production-only stream_error; it falls back to mock.
    assert "stream_error" not in event_names
    assert flat[0]["event"] == "snapshot"
    assert flat[0]["data"]["provenance"] == "mock"
    assert flat[0]["data"]["source_status"] == "synthetic"
