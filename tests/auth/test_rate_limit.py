"""Tests for L7: in-memory rate limiter."""
from __future__ import annotations

from packages.auth.rate_limit import InMemoryRateLimiter


def test_allows_requests_within_limit():
    limiter = InMemoryRateLimiter(max_requests=5, window_seconds=60)
    for _ in range(5):
        assert limiter.is_allowed("client_1") is True


def test_blocks_requests_exceeding_limit():
    limiter = InMemoryRateLimiter(max_requests=3, window_seconds=60)
    for _ in range(3):
        assert limiter.is_allowed("client_1") is True
    assert limiter.is_allowed("client_1") is False


def test_separate_keys_independent():
    limiter = InMemoryRateLimiter(max_requests=2, window_seconds=60)
    assert limiter.is_allowed("client_1") is True
    assert limiter.is_allowed("client_1") is True
    assert limiter.is_allowed("client_1") is False
    # client_2 should still be allowed
    assert limiter.is_allowed("client_2") is True


def test_reset_clears_state():
    limiter = InMemoryRateLimiter(max_requests=2, window_seconds=60)
    limiter.is_allowed("client_1")
    limiter.is_allowed("client_1")
    limiter.reset("client_1")
    assert limiter.is_allowed("client_1") is True


def test_reset_all_clears_everything():
    limiter = InMemoryRateLimiter(max_requests=1, window_seconds=60)
    limiter.is_allowed("a")
    limiter.is_allowed("b")
    limiter.reset()
    assert limiter.is_allowed("a") is True
    assert limiter.is_allowed("b") is True
