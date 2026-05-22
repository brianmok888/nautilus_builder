from __future__ import annotations

from packages.backtest_jobs.service import BacktestJobService


def test_frontend_disconnect_does_not_cancel_job() -> None:
    service = BacktestJobService()
    job = service.create_job(
        {
            "strategy_spec_version": "0.1.0-draft.1",
            "adapter_id": "BINANCE_PERP",
            "instrument_id": "BTCUSDT-PERP",
            "compile_hash": "abc123",
            "validation_report_id": "vr_001",
        }
    )

    service.transition_job(job.job_id, "RUNNING")
    service.record_frontend_disconnect(job.job_id)

    stored = service.get_job(job.job_id)

    assert stored.stage == "RUNNING"
    assert stored.cancel_requested is False


def test_cancel_request_changes_backend_state() -> None:
    service = BacktestJobService()
    job = service.create_job(
        {
            "strategy_spec_version": "0.1.0-draft.1",
            "adapter_id": "BINANCE_PERP",
            "instrument_id": "BTCUSDT-PERP",
            "compile_hash": "abc123",
            "validation_report_id": "vr_001",
        }
    )

    service.request_cancel(job.job_id)

    stored = service.get_job(job.job_id)
    assert stored.stage == "CANCEL_REQUESTED"
    assert stored.cancel_requested is True
