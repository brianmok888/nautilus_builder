"""Test AI builder rate limiter and auth gate on draft endpoint."""
from __future__ import annotations

from packages.ai_builder.rate_limiter import TokenBucketRateLimiter


def test_rate_limiter_allows_within_capacity() -> None:
    limiter = TokenBucketRateLimiter(max_tokens=3, refill_period_secs=60.0)
    assert limiter.allow("key_1") is True
    assert limiter.allow("key_1") is True
    assert limiter.allow("key_1") is True


def test_rate_limiter_rejects_over_capacity() -> None:
    limiter = TokenBucketRateLimiter(max_tokens=2, refill_period_secs=60.0)
    limiter.allow("key_1")
    limiter.allow("key_1")
    assert limiter.allow("key_1") is False


def test_rate_limiter_isolation_per_key() -> None:
    limiter = TokenBucketRateLimiter(max_tokens=1, refill_period_secs=60.0)
    assert limiter.allow("key_a") is True
    assert limiter.allow("key_b") is True


def test_tokens_remaining_reports_correctly() -> None:
    limiter = TokenBucketRateLimiter(max_tokens=3, refill_period_secs=60.0)
    assert limiter.tokens_remaining("key_1") == 3.0
    limiter.allow("key_1")
    assert limiter.tokens_remaining("key_1") < 3.0
