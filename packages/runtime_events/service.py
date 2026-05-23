from __future__ import annotations

from packages.runtime_events.models import RuntimeEvent
from packages.runtime_events.stream import InMemoryRuntimeEventStream


class RuntimeEventService:
    def __init__(self, *, stream: InMemoryRuntimeEventStream | None = None) -> None:
        self._stream = stream or InMemoryRuntimeEventStream()

    def append_event(
        self,
        *,
        job_id: str,
        stage: str,
        level: str,
        message: str,
        progress_pct: float,
    ) -> RuntimeEvent:
        event = RuntimeEvent(
            job_id=job_id,
            stage=stage,
            level=level,
            message=message,
            progress_pct=progress_pct,
        )
        self._stream.append(event)
        return event

    def replay_events(self, job_id: str) -> list[RuntimeEvent]:
        return self._stream.replay(job_id)
