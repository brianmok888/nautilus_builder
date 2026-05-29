"""Simple in-memory rate limiter for API routes (L7).

No third-party dependencies. Uses a sliding window counter per client IP.
For production, replace with Redis-backed or nginx-level rate limiting.
"""
from __future__ import annotations

import time
from collections import defaultdict


class InMemoryRateLimiter:
    """Sliding window rate limiter keyed by client identifier."""

    def __init__(self, max_requests: int = 100, window_seconds: int = 60) -> None:
        self._max_requests = max_requests
        self._window_seconds = window_seconds
        self._windows: dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, key: str) -> bool:
        """Check if a request from key is within rate limits.

        Returns True if allowed, False if rate limited.
        """
        now = time.monotonic()
        window = self._windows[key]
        cutoff = now - self._window_seconds

        # Remove expired entries
        while window and window[0] < cutoff:
            window.pop(0)

        if len(window) >= self._max_requests:
            return False

        window.append(now)
        return True

    def reset(self, key: str | None = None) -> None:
        """Reset rate limit state for a key, or all keys."""
        if key is None:
            self._windows.clear()
        else:
            self._windows.pop(key, None)
