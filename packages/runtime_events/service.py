from __future__ import annotations

from packages.runtime_events.models import RuntimeEvent


class RuntimeEventService:
    def __init__(self) -> None:
        self._events: dict[str, list[RuntimeEvent]] = {}

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
        self._events.setdefault(job_id, []).append(event)
        return event

    def replay_events(self, job_id: str) -> list[RuntimeEvent]:
        return list(self._events.get(job_id, []))
