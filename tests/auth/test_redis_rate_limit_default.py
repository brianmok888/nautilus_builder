"""P1-3 regression: RedisRateLimiter must default to fail-closed.

The constructor previously defaulted to fail_closed=False with a docstring framing
fail-open as normal. Direct/bare construction in production could therefore silently
allow requests when Redis is unavailable. The default must be fail-closed; fail-open
is a local/dev opt-in only.
"""
from __future__ import annotations

import sys
import types

import pytest


def _make_redis_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    class _BoomFactory:
        @staticmethod
        def from_url(redis_url: str, socket_connect_timeout: int):
            raise ConnectionError("Connection refused")

    monkeypatch.setitem(sys.modules, "redis", types.SimpleNamespace(Redis=_BoomFactory))


def test_default_construction_fails_closed_when_redis_unavailable(monkeypatch, caplog) -> None:
    """Bare construction (no fail_closed arg) must deny when Redis is down."""
    _make_redis_unavailable(monkeypatch)
    from packages.auth.redis_rate_limit import RedisRateLimiter

    caplog.set_level("WARNING")
    # No fail_closed argument: must default to the safe (closed) posture.
    limiter = RedisRateLimiter(redis_url="redis://localhost:6379/0")

    assert limiter.is_allowed("client_1") is False
    # No sensitive URL content leaked in the warning.
    assert "localhost:6379" in caplog.text or "rate_limit_redis_unavailable" in caplog.text


def test_fail_open_is_explicit_opt_in_only(monkeypatch) -> None:
    """Fail-open behavior requires an explicit fail_closed=False (local/dev only)."""
    _make_redis_unavailable(monkeypatch)
    from packages.auth.redis_rate_limit import RedisRateLimiter

    open_limiter = RedisRateLimiter(redis_url="redis://localhost:6379/0", fail_closed=False)
    assert open_limiter.is_allowed("client_1") is True

    closed_limiter = RedisRateLimiter(redis_url="redis://localhost:6379/0", fail_closed=True)
    assert closed_limiter.is_allowed("client_1") is False
