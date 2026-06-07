"""Tests for Redis-backed rate limiter.

TDD RED phase: these tests define the expected behavior of RedisRateLimiter
before implementation exists.
"""
from __future__ import annotations

from unittest.mock import MagicMock



class TestRedisRateLimiter:
    """RedisRateLimiter uses Redis INCR + EXPIRE for sliding window counting."""

    def _make_limiter(self, max_requests: int = 5, window_seconds: int = 60, redis_url: str = "redis://localhost:6379/0"):
        from packages.auth.redis_rate_limit import RedisRateLimiter
        return RedisRateLimiter(max_requests=max_requests, window_seconds=window_seconds, redis_url=redis_url)

    def test_import_exists(self):
        """RedisRateLimiter can be imported."""
        from packages.auth.redis_rate_limit import RedisRateLimiter
        assert RedisRateLimiter is not None

    def test_is_allowed_within_limit(self):
        """Requests within limit are allowed."""
        limiter = self._make_limiter(max_requests=3, window_seconds=60)
        mock_redis = MagicMock()
        mock_redis.incr.return_value = 1
        mock_redis.expire.return_value = True
        limiter._redis = mock_redis

        assert limiter.is_allowed("client_1") is True

    def test_is_allowed_at_limit(self):
        """Request at exactly the limit is allowed."""
        limiter = self._make_limiter(max_requests=3, window_seconds=60)
        mock_redis = MagicMock()
        mock_redis.incr.return_value = 3
        mock_redis.expire.return_value = True
        limiter._redis = mock_redis

        assert limiter.is_allowed("client_1") is True

    def test_is_allowed_over_limit(self):
        """Requests over limit are rejected."""
        limiter = self._make_limiter(max_requests=3, window_seconds=60)
        mock_redis = MagicMock()
        mock_redis.incr.return_value = 4
        mock_redis.expire.return_value = True
        limiter._redis = mock_redis

        assert limiter.is_allowed("client_1") is False

    def test_is_allowed_isolation_per_key(self):
        """Different keys have independent counters."""
        limiter = self._make_limiter(max_requests=1, window_seconds=60)
        mock_redis = MagicMock()
        # First key: count = 1 (allowed)
        # Second key: count = 1 (allowed)
        mock_redis.incr.return_value = 1
        mock_redis.expire.return_value = True
        limiter._redis = mock_redis

        assert limiter.is_allowed("key_a") is True
        assert limiter.is_allowed("key_b") is True

    def test_fails_open_when_redis_unavailable(self):
        """When Redis is unreachable, rate limiter allows request and logs warning."""
        limiter = self._make_limiter(max_requests=3, window_seconds=60)
        mock_redis = MagicMock()
        mock_redis.incr.side_effect = Exception("Connection refused")
        limiter._redis = mock_redis

        # Should NOT raise, should return True (fail open)
        assert limiter.is_allowed("client_1") is True

    def test_uses_sliding_window_key_format(self):
        """Redis key includes the window bucket for sliding window semantics."""
        limiter = self._make_limiter(max_requests=5, window_seconds=60)
        mock_redis = MagicMock()
        mock_redis.incr.return_value = 1
        mock_redis.expire.return_value = True
        limiter._redis = mock_redis

        limiter.is_allowed("192.168.1.1")

        # Verify the key passed to Redis includes rate_limit prefix
        call_args = mock_redis.incr.call_args
        assert call_args is not None
        key = call_args[0][0]
        assert "rate_limit" in key
        assert "192.168.1.1" in key

    def test_expire_called_on_new_window(self):
        """EXPIRE is set on the key to ensure window cleanup."""
        limiter = self._make_limiter(max_requests=5, window_seconds=60)
        mock_redis = MagicMock()
        mock_redis.incr.return_value = 1
        mock_redis.expire.return_value = True
        limiter._redis = mock_redis

        limiter.is_allowed("client_1")

        mock_redis.expire.assert_called()


class TestInMemoryRateLimiterStillWorks:
    """Verify InMemoryRateLimiter is unaffected by Redis addition."""

    def test_in_memory_allows(self):
        from packages.auth.rate_limit import InMemoryRateLimiter
        limiter = InMemoryRateLimiter(max_requests=3, window_seconds=60)
        assert limiter.is_allowed("key") is True
        assert limiter.is_allowed("key") is True
        assert limiter.is_allowed("key") is True

    def test_in_memory_rejects_over_limit(self):
        from packages.auth.rate_limit import InMemoryRateLimiter
        limiter = InMemoryRateLimiter(max_requests=2, window_seconds=60)
        limiter.is_allowed("key")
        limiter.is_allowed("key")
        assert limiter.is_allowed("key") is False
