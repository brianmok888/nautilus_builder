from __future__ import annotations

import threading
import time
from collections import defaultdict


class TokenBucketRateLimiter:
    """Simple in-memory token bucket rate limiter.

    Thread-safe. Each key (e.g., user_id or IP) gets its own bucket.
    """

    def __init__(
        self,
        *,
        max_tokens: int = 10,
        refill_period_secs: float = 60.0,
    ) -> None:
        self._max_tokens = max_tokens
        self._refill_period_secs = refill_period_secs
        self._refill_rate = max_tokens / refill_period_secs
        self._buckets: dict[str, tuple[float, float]] = defaultdict(lambda: (float(max_tokens), time.monotonic()))
        self._lock = threading.Lock()

    def allow(self, key: str) -> bool:
        with self._lock:
            tokens, last_refill = self._buckets[key]
            now = time.monotonic()
            elapsed = now - last_refill
            current = min(self._max_tokens, tokens + elapsed * self._refill_rate)
            if current < 1.0:
                self._buckets[key] = (current, now)
                return False
            self._buckets[key] = (current - 1.0, now)
            return True

    def tokens_remaining(self, key: str) -> float:
        with self._lock:
            tokens, last_refill = self._buckets[key]
            now = time.monotonic()
            elapsed = now - last_refill
            return min(self._max_tokens, tokens + elapsed * self._refill_rate)


DEFAULT_AI_BUILDER_RATE_LIMITER = TokenBucketRateLimiter(max_tokens=10, refill_period_secs=60.0)
