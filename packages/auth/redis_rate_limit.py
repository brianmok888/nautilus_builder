"""Redis-backed rate limiter for production API routes (L7).

Uses Redis INCR + EXPIRE for sliding window counting per client key.

Fail-closed by default: when Redis is unavailable or a Redis command fails, the
limiter DENIES the request and logs a warning. Fail-open behavior (allow on Redis
failure) is a local/dev opt-in only via ``fail_closed=False`` and must never be
used in production. For local development, prefer ``InMemoryRateLimiter``.
"""
from __future__ import annotations

import logging
import time
from typing import Any
from urllib.parse import urlsplit, urlunsplit

logger = logging.getLogger(__name__)


class RedisRateLimiter:
    """Sliding window rate limiter backed by Redis.

    Uses INCR + EXPIRE for atomic counting. Fails closed (denies the request)
    when Redis is unavailable; pass ``fail_closed=False`` to opt into fail-open
    behavior for local/dev only.
    """

    def __init__(
        self,
        max_requests: int = 100,
        window_seconds: int = 60,
        redis_url: str = "redis://localhost:6379/0",
        fail_closed: bool = True,
    ) -> None:
        self._max_requests = max_requests
        self._window_seconds = window_seconds
        self._redis_url = redis_url
        self._fail_closed = fail_closed
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
                "falling_back_to_%s",
                _redact_redis_url(redis_url),
                exc,
                "closed" if self._fail_closed else "open",
            )
            return None

    def is_allowed(self, key: str) -> bool:
        """Check if a request from key is within rate limits.

        Returns True if allowed, False if rate limited.
        Fails open by default and closed when configured for production.
        """
        if self._redis is None:
            return not self._fail_closed

        now = time.time()
        window_key = f"rate_limit:{key}:{int(now // self._window_seconds)}"

        try:
            count = self._redis.incr(window_key)
            if count == 1:
                self._redis.expire(window_key, self._window_seconds)
            return count <= self._max_requests
        except Exception as exc:
            logger.warning(
                "rate_limit_fallback_%s key=%s error=%s",
                "closed" if self._fail_closed else "open",
                key,
                exc,
            )
            return not self._fail_closed


def _redact_redis_url(redis_url: str) -> str:
    parsed = urlsplit(redis_url)
    if "@" not in parsed.netloc:
        return redis_url
    host = parsed.hostname or ""
    port = f":{parsed.port}" if parsed.port is not None else ""
    return urlunsplit((parsed.scheme, f"***@{host}{port}", parsed.path, parsed.query, parsed.fragment))
