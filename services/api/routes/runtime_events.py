from __future__ import annotations

from packages.runtime_events.service import RuntimeEventService


def replay_runtime_events_payload() -> list[dict[str, object]]:
    service = RuntimeEventService()
    service.append_event(
        job_id="bt_001",
        stage="RUNNING",
        level="INFO",
        message="Processed 2025-03-01 to 2025-03-15",
        progress_pct=52.4,
    )
    service.append_event(
        job_id="bt_001",
        stage="RUNNING",
        level="INFO",
        message="Processed 2025-03-16 to 2025-03-31",
        progress_pct=74.2,
    )
    return [event.model_dump(mode="json") for event in service.replay_events("bt_001")]
