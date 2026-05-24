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


def test_runtime_event_records_hardguard_audit_fields() -> None:
    service = RuntimeEventService()

    event = service.append_event(
        job_id="bt_001",
        actor_type="worker",
        actor_id="worker_001",
        stage="RUNNING",
        level="INFO",
        message="Backtest worker started",
        progress_pct=0.0,
        metadata={"worker_image": "nautilus-builder-worker:dev"},
    )

    assert event.event_id == "bt_001_evt_000001"
    assert event.job_id == "bt_001"
    assert event.actor_type == "worker"
    assert event.actor_id == "worker_001"
    assert event.stage == "RUNNING"
    assert event.level == "INFO"
    assert event.message == "Backtest worker started"
    assert event.timestamp
    assert event.metadata["worker_image"] == "nautilus-builder-worker:dev"
    assert event.metadata["progress_pct"] == 0.0
