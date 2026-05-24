from __future__ import annotations

from datetime import UTC, datetime

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
        actor_type: str = "system",
        actor_id: str = "builder-runtime",
        metadata: dict[str, object] | None = None,
    ) -> RuntimeEvent:
        sequence = len(self._stream.replay(job_id)) + 1
        event_metadata = dict(metadata or {})
        event_metadata.setdefault("progress_pct", progress_pct)
        event = RuntimeEvent(
            event_id=f"{job_id}_evt_{sequence:06d}",
            job_id=job_id,
            actor_type=actor_type,
            actor_id=actor_id,
            stage=stage,
            level=level,
            message=message,
            timestamp=datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            metadata=event_metadata,
            progress_pct=progress_pct,
        )
        self._stream.append(event)
        return event

    def replay_events(self, job_id: str) -> list[RuntimeEvent]:
        return self._stream.replay(job_id)
