"""Redis-backed rate limiter for production API routes (L7).

Uses Redis INCR + EXPIRE for sliding window counting per client key.
Fails open (allows request, logs warning) when Redis is unavailable.
For local development, use InMemoryRateLimiter instead.
"""
from __future__ import annotations

import logging
import time
from typing import Any

logger = logging.getLogger(__name__)


class RedisRateLimiter:
    """Sliding window rate limiter backed by Redis.

    Uses INCR + EXPIRE for atomic counting. Fails open when Redis
    is unavailable, allowing requests through with a logged warning.
    """

    def __init__(
        self,
        max_requests: int = 100,
        window_seconds: int = 60,
        redis_url: str = "redis://localhost:6379/0",
    ) -> None:
        self._max_requests = max_requests
        self._window_seconds = window_seconds
        self._redis_url = redis_url
        self._redis: Any = self._connect(redis_url)

    def _connect(self, redis_url: str) -> Any:
        """Connect to Redis. Returns None if unavailable."""
        try:
            import redis
            client = redis.Redis.from_url(redis_url, socket_connect_timeout=2)
            client.ping()
            return client
        except Exception as exc:
            logger.warning(
                "rate_limit_redis_unavailable url=%s error=%s "
                "falling_back_to_open",
                redis_url,
                exc,
            )
            return None

    def is_allowed(self, key: str) -> bool:
        """Check if a request from key is within rate limits.

        Returns True if allowed, False if rate limited.
        Fails open (returns True) if Redis is unavailable.
        """
        if self._redis is None:
            return True

        now = time.time()
        window_key = f"rate_limit:{key}:{int(now // self._window_seconds)}"

        try:
            count = self._redis.incr(window_key)
            if count == 1:
                self._redis.expire(window_key, self._window_seconds)
            return count <= self._max_requests
        except Exception as exc:
            logger.warning(
                "rate_limit_fallback_open key=%s error=%s",
                key,
                exc,
            )
            return True
