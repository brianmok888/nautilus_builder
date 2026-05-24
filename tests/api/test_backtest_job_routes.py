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
        "created_by": "operator_001",
        "data_range": "2024-01-01:2024-03-01",
    }

    created = app.post("/api/backtest-jobs", json=payload)
    job_id = created.json()["job_id"]
    detail = app.get(f"/api/backtest-jobs/{job_id}")
    cancelled = app.post(f"/api/backtest-jobs/{job_id}/cancel", json={})

    assert created.status_code == 201
    assert job_id == created.json()["backend_job_id"]
    assert detail.json()["status"] == "queued"
    assert detail.json()["created_by"] == "operator_001"
    assert detail.json()["strategy_spec_version_id"] == "strategy_001_v001"
    assert detail.json()["adapter_profile_id"] == "profile_001"
    assert detail.json()["data_range"] == "2024-01-01:2024-03-01"
    assert detail.json()["worker_id"] == "unassigned"
    assert detail.json()["result_artifact_refs"] == {}
    assert detail.json()["event_stream_id"] == f"builder:runtime:{job_id}"
    assert cancelled.json()["status"] == "cancel_requested"
    assert app.get(f"/api/backtest-jobs/{job_id}").json()["status"] == "cancel_requested"


def test_backtest_job_unknown_ids_return_404_instead_of_static_payloads() -> None:
    app = create_app()

    detail = app.get("/api/backtest-jobs/missing-job")
    cancelled = app.post("/api/backtest-jobs/missing-job/cancel", json={})

    assert detail.status_code == 404
    assert detail.json()["error"] == "backtest_job_not_found"
    assert cancelled.status_code == 404
    assert cancelled.json()["error"] == "backtest_job_not_found"


def test_backtest_job_events_are_observable_without_nd_stream_ownership() -> None:
    app = create_app()
    response = app.get("/api/backtest-jobs/bt_job_001/events")

    assert response.status_code == 200
    assert response.json()["stream_name"] == "builder:runtime:bt_job_001"
    assert response.json()["mode"] == "observational"
    assert response.json()["status"] == "observing"
    assert response.json()["events"] == []
