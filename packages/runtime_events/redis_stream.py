from __future__ import annotations

import os
from typing import Any

from packages.runtime_events.models import RuntimeEvent


class RedisRuntimeEventStream:
    STREAM_PATTERN = "builder:runtime:{job_id}"

    def __init__(self, *, client: Any, namespace: str = "builder") -> None:
        if namespace != "builder":
            raise ValueError("Builder runtime stream requires builder namespace")
        self._client = client
        self._namespace = namespace

    def append(self, event: RuntimeEvent) -> None:
        self._client.xadd(self._stream_name(event.job_id), event.model_dump(mode="json"))

    def replay(self, job_id: str) -> list[RuntimeEvent]:
        return [RuntimeEvent(**payload) for _, payload in self._client.xrange(self._stream_name(job_id))]

    def _stream_name(self, job_id: str) -> str:
        return self.STREAM_PATTERN.format(job_id=job_id)


def connect_builder_redis(url_env: str = "BUILDER_REDIS_URL") -> Any:
    url = os.getenv(url_env)
    if not url:
        raise ValueError(f"Redis URL environment variable is not configured: {url_env}")
    try:
        import redis
    except ImportError as exc:
        raise RuntimeError("redis is required for real Builder Redis streams") from exc
    return redis.Redis.from_url(url, decode_responses=True)
