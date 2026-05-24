from __future__ import annotations

from packages.backtest_jobs.service import BacktestJobService
from packages.backtest_runner.runner import run_backtest_fixture
from packages.backtest_runner.artifacts import BacktestResultArtifact
from packages.runtime_events.service import RuntimeEventService


def run_worker_fixture() -> dict[str, object]:
    result = run_backtest_fixture(
        strategy_spec_version="0.1.0-draft.1",
        adapter_id="BINANCE_PERP",
        instrument_id="BTCUSDT-PERP",
        compile_hash="fixture",
        worker_image="nautilus-builder-worker:dev",
    )
    return result.model_dump(mode="json")


def run_backtest_job(
    *,
    job_id: str,
    jobs: BacktestJobService,
    events: RuntimeEventService,
    worker_image: str,
) -> BacktestResultArtifact | None:
    job = jobs.get_job(job_id)
    if job.cancel_requested:
        events.append_event(
            job_id=job.job_id,
            actor_type="worker",
            actor_id=worker_image,
            stage="CANCEL_REQUESTED",
            level="INFO",
            message="Backtest cancellation observed before worker start",
            progress_pct=0.0,
            metadata={"worker_image": worker_image},
        )
        return None

    jobs.transition_job(job.job_id, "RUNNING", worker_id=worker_image)
    events.append_event(
        job_id=job.job_id,
        actor_type="worker",
        actor_id=worker_image,
        stage="RUNNING",
        level="INFO",
        message="Backtest worker started",
        progress_pct=0.0,
        metadata={"worker_image": worker_image},
    )
    result = run_backtest_fixture(
        backtest_job_id=job.job_id,
        strategy_spec_version=job.strategy_spec_version_id,
        adapter_id=job.adapter_profile_id,
        instrument_id=job.instrument_id,
        compile_hash=job.compile_hash,
        worker_image=worker_image,
    )
    jobs.transition_job(job.job_id, "SUCCEEDED", worker_id=worker_image, result_artifact_refs=result.artifact_refs)
    events.append_event(
        job_id=job.job_id,
        actor_type="worker",
        actor_id=worker_image,
        stage="SUCCEEDED",
        level="INFO",
        message="Backtest worker succeeded",
        progress_pct=100.0,
        metadata={"worker_image": worker_image, "artifact_refs": result.artifact_refs},
    )
    return result
