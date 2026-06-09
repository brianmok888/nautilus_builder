from __future__ import annotations


def test_redis_rate_limit_logs_redacted_url() -> None:
    from packages.auth.redis_rate_limit import _redact_redis_url

    redacted = _redact_redis_url("redis://:super-secret@redis.internal:6379/0")

    assert "super-secret" not in redacted
    assert redacted == "redis://***@redis.internal:6379/0"
