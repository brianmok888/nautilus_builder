from __future__ import annotations

from services.api.app import create_app


def test_backtest_job_can_be_created_read_and_cancelled() -> None:
    app = create_app()
    payload = {
        "strategy_version_id": "strategy_001_v001",
        "strategy_lineage_id": "lineage_strategy_001",
        "adapter_profile_id": "profile_001",
        "instrument_id": "BTCUSDT-PERP",
        "validation_report_id": "validation_001",
        "compile_artifact_id": "compile_001",
    }

    created = app.post("/api/backtest-jobs", json=payload)
    detail = app.get("/api/backtest-jobs/bt_job_001")
    cancelled = app.post("/api/backtest-jobs/bt_job_001/cancel", json={})

    assert created.status_code == 201
    assert created.json()["job_id"] == "bt_job_001"
    assert detail.json()["status"] == "queued"
    assert cancelled.json()["status"] == "cancel_requested"


def test_backtest_job_events_are_observable_without_nd_stream_ownership() -> None:
    app = create_app()
    response = app.get("/api/backtest-jobs/bt_job_001/events")

    assert response.status_code == 200
    assert response.json()["stream_name"] == "builder:runtime:bt_job_001"
    assert response.json()["mode"] == "observational"
