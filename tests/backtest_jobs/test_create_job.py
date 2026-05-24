from __future__ import annotations

from packages.backtest_jobs.service import BacktestJobService


def test_job_creation_is_idempotent() -> None:
    service = BacktestJobService()

    payload = {
        "strategy_spec_version": "0.1.0-draft.1",
        "adapter_id": "BINANCE_PERP",
        "instrument_id": "BTCUSDT-PERP",
        "compile_hash": "abc123",
        "validation_report_id": "vr_001",
    }

    first = service.create_job(payload)
    second = service.create_job(payload)

    assert first.job_id == second.job_id
    assert first.stage == "CREATED"
    assert first.compile_hash == "abc123"


def test_job_creation_records_hardguard_audit_fields() -> None:
    service = BacktestJobService()

    job = service.create_job(
        {
            "strategy_spec_version_id": "strategy_001_v001",
            "adapter_profile_id": "profile_BINANCE_PERP",
            "instrument_id": "BTCUSDT-PERP",
            "compile_hash": "compile_001",
            "validation_report_id": "validation_001",
            "created_by": "operator_001",
            "data_range": "2024-01-01:2024-03-01",
        }
    )

    assert job.status == "CREATED"
    assert job.stage == "CREATED"
    assert job.created_by == "operator_001"
    assert job.created_at
    assert job.updated_at
    assert job.strategy_spec_version_id == "strategy_001_v001"
    assert job.adapter_profile_id == "profile_BINANCE_PERP"
    assert job.instrument_id == "BTCUSDT-PERP"
    assert job.data_range == "2024-01-01:2024-03-01"
    assert job.worker_id == "unassigned"
    assert job.result_artifact_refs == {}
    assert job.event_stream_id == f"builder:runtime:{job.job_id}"
