from __future__ import annotations

import json

from packages.runtime_events.service import RuntimeEventService


def replay_runtime_events_payload(
    *,
    service: RuntimeEventService | None = None,
    job_id: str = "bt_001",
) -> list[dict[str, object]]:
    service = service or _fixture_service(job_id)
    return [event.model_dump(mode="json") for event in service.replay_events(job_id)]


def runtime_events_sse_payload(
    *,
    service: RuntimeEventService,
    job_id: str,
) -> list[str]:
    return [
        f"event: runtime_event\ndata: {json.dumps(event.model_dump(mode='json'), sort_keys=True, separators=(',', ':'))}\n"
        for event in service.replay_events(job_id)
    ]


def _fixture_service(job_id: str) -> RuntimeEventService:
    service = RuntimeEventService()
    service.append_event(
        job_id=job_id,
        stage="RUNNING",
        level="INFO",
        message="Processed 2025-03-01 to 2025-03-15",
        progress_pct=52.4,
    )
    service.append_event(
        job_id=job_id,
        stage="RUNNING",
        level="INFO",
        message="Processed 2025-03-16 to 2025-03-31",
        progress_pct=74.2,
    )
    return service
