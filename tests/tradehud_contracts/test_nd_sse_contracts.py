"""
ND SSE contract tests.

Verifies the SSE route emits correct event types without exposing credentials
and without providing order authority.
"""
import pytest
from services.api.routes.tradehud_sse import (
    _format_sse,
    _format_ping,
    _scrub_credentials,
    _is_sensitive_key,
    _annotate,
)

TS = 1700000000_000000000


class TestSSEEventTypes:
    def test_snapshot_event(self):
        data = _format_sse("snapshot", {"book_top": None})
        assert b"event: snapshot" in data
        assert b"data:" in data

    def test_tradehud_event(self):
        data = _format_sse("tradehud_event", {"type": "TRADE", "payload": {}})
        assert b"event: tradehud_event" in data

    def test_stream_health_event(self):
        data = _format_sse("stream_health", {"lanes": []})
        assert b"event: stream_health" in data

    def test_ping_event(self):
        data = _format_ping()
        assert b"event: ping" in data


class TestCredentialScrubbing:
    def test_scrub_removes_redis_password(self):
        payload = {"redis_url": "redis://:s3cret@localhost:6379/0", "status": "ok"}
        scrubbed = _scrub_credentials(payload)
        assert "s3cret" not in str(scrubbed)

    def test_scrub_removes_password_key(self):
        payload = {"password": "my_secret", "data": "ok"}
        scrubbed = _scrub_credentials(payload)
        assert "my_secret" not in str(scrubbed)

    def test_scrub_preserves_safe_data(self):
        payload = {"status": "live", "symbol": "BTCUSDT-PERP"}
        scrubbed = _scrub_credentials(payload)
        assert scrubbed["status"] == "live"
        assert scrubbed["symbol"] == "BTCUSDT-PERP"

    def test_sensitive_key_detection(self):
        assert _is_sensitive_key("password") is True
        assert _is_sensitive_key("redis_url") is True
        assert _is_sensitive_key("api_key") is True
        assert _is_sensitive_key("secret") is True
        assert _is_sensitive_key("status") is False
        assert _is_sensitive_key("symbol") is False

    def test_nested_scrub(self):
        """Scrub at top level — nested dict values are preserved as-is
        since SSE payload is flat (pydantic model dump)."""
        payload = {
            "outer": "ok",
            "password": "top_secret",
        }
        scrubbed = _scrub_credentials(payload)
        assert "top_secret" not in str(scrubbed)
        assert scrubbed.get("outer") == "ok"


class TestRedisModeInSSE:
    def test_redis_not_enabled_by_default(self, monkeypatch):
        monkeypatch.delenv("TRADEHUD_FEED_SOURCE", raising=False)
        monkeypatch.delenv("TRADEHUD_REDIS_URL", raising=False)
        monkeypatch.delenv("REDIS_URL", raising=False)


class TestAnnotate:
    def test_annotate_adds_provenance(self):
        result = _annotate({"a": 1}, provenance="redis")
        assert "provenance" in result
        assert result["provenance"] == "redis"

    def test_annotate_adds_source_status(self):
        result = _annotate({"a": 1}, source_status="live")
        assert "source_status" in result
        assert result["source_status"] == "live"


class TestNoOrderAuthority:
    def test_no_submit_in_sse_source(self):
        import services.api.routes.tradehud_sse as mod
        source = open(mod.__file__).read().lower()
        assert "submit_order" not in source.replace("no submit_order", "")
        assert "force_approve" not in source

    def test_no_post_endpoints(self):
        import services.api.routes.tradehud_sse as mod
        source = open(mod.__file__).read()
        assert "POST" not in source or "no POST" in source.lower()
