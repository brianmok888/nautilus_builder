from __future__ import annotations

from packages.runtime_events.service import RuntimeEventService


def test_runtime_events_can_be_replayed_after_reconnect() -> None:
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

    replayed = service.replay_events("bt_001")

    assert len(replayed) == 2
    assert replayed[0].message == "Processed 2025-03-01 to 2025-03-15"
    assert replayed[1].progress_pct == 74.2
