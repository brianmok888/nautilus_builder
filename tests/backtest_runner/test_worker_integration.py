from __future__ import annotations

from packages.backtest_jobs.service import BacktestJobService
from packages.runtime_events.service import RuntimeEventService
from services.workers.nautilus_backtest_worker import run_backtest_job


def test_worker_loads_backend_job_emits_events_and_persists_result_identity() -> None:
    jobs = BacktestJobService()
    events = RuntimeEventService()
    job = jobs.create_job(
        {
            "strategy_spec_version": "0.1.0-draft.1",
            "adapter_id": "BINANCE_PERP",
            "instrument_id": "BTCUSDT-PERP",
            "compile_hash": "abc123",
            "validation_report_id": "vr_001",
        }
    )

    result = run_backtest_job(job_id=job.job_id, jobs=jobs, events=events, worker_image="nautilus-builder-worker:dev")

    assert jobs.get_job(job.job_id).stage == "SUCCEEDED"
    assert result.backtest_job_id == job.job_id
    assert result.compile_hash == "abc123"
    assert [event.stage for event in events.replay_events(job.job_id)] == ["RUNNING", "SUCCEEDED"]
    assert jobs.get_job(job.job_id).worker_id == "nautilus-builder-worker:dev"
    assert jobs.get_job(job.job_id).result_artifact_refs == result.artifact_refs


def test_worker_honors_cancel_requested_before_running() -> None:
    jobs = BacktestJobService()
    events = RuntimeEventService()
    job = jobs.create_job(
        {
            "strategy_spec_version": "0.1.0-draft.1",
            "adapter_id": "BINANCE_PERP",
            "instrument_id": "BTCUSDT-PERP",
            "compile_hash": "abc123",
            "validation_report_id": "vr_001",
        }
    )
    jobs.request_cancel(job.job_id)

    result = run_backtest_job(job_id=job.job_id, jobs=jobs, events=events, worker_image="nautilus-builder-worker:dev")

    assert result is None
    assert jobs.get_job(job.job_id).stage == "CANCEL_REQUESTED"
    assert events.replay_events(job.job_id)[0].message == "Backtest cancellation observed before worker start"
