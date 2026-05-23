from __future__ import annotations

import sys
import types

import pytest

from packages.runtime_events.models import RuntimeEvent
from packages.runtime_events.redis_stream import RedisRuntimeEventStream, connect_builder_redis
from services.api.sse import format_runtime_event_sse


class FakeRedisClient:
    def __init__(self) -> None:
        self.entries: list[tuple[str, dict[str, str]]] = []

    def xadd(self, stream_name: str, payload: dict[str, str]) -> str:
        self.entries.append((stream_name, payload))
        return "1-0"

    def xrange(self, stream_name: str):
        return [("1-0", payload) for name, payload in self.entries if name == stream_name]


def test_redis_stream_publishes_and_replays_builder_owned_runtime_events() -> None:
    client = FakeRedisClient()
    stream = RedisRuntimeEventStream(client=client, namespace="builder")
    event = RuntimeEvent(job_id="bt_001", stage="RUNNING", level="INFO", message="started", progress_pct=1.0)

    stream.append(event)

    assert client.entries[0][0] == "builder:runtime:bt_001"
    assert stream.replay("bt_001") == [event]


def test_redis_connection_uses_url_from_environment(monkeypatch) -> None:
    received: list[str] = []

    class Redis:
        @staticmethod
        def from_url(url: str, decode_responses: bool):
            received.append(url)
            assert decode_responses is True
            return object()

    monkeypatch.setenv("BUILDER_REDIS_URL", "redis://localhost:6379/0")
    monkeypatch.setitem(sys.modules, "redis", types.SimpleNamespace(Redis=Redis))

    assert connect_builder_redis("BUILDER_REDIS_URL") is not None
    assert received == ["redis://localhost:6379/0"]


def test_redis_connection_requires_configured_url(monkeypatch) -> None:
    monkeypatch.delenv("BUILDER_REDIS_URL", raising=False)
    with pytest.raises(ValueError, match="Redis URL environment variable is not configured"):
        connect_builder_redis("BUILDER_REDIS_URL")


def test_sse_formats_runtime_event_for_observational_delivery() -> None:
    event = RuntimeEvent(job_id="bt_001", stage="COMPLETED", level="INFO", message="finished", progress_pct=100.0)

    formatted = format_runtime_event_sse(event)

    assert formatted.startswith("event: runtime_event\n")
    assert '"stage":"COMPLETED"' in formatted
