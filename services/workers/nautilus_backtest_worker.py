from __future__ import annotations

from packages.backtest_jobs.service import BacktestJobService
from packages.backtest_runner.runner import run_backtest_fixture
from packages.backtest_runner.artifacts import BacktestResultArtifact
from packages.backtest_runner.strategy_spec_replay import run_strategy_spec_catalog_replay
from packages.artifact_store import LocalJsonArtifactStore
from packages.auth import UserProjectContext
from pathlib import Path

from packages.catalog_datasets import CatalogDataset
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
    context: UserProjectContext | None = None,
    artifact_store: LocalJsonArtifactStore | None = None,
    strategy_spec_payload: dict[str, object] | None = None,
    catalog_dataset: CatalogDataset | None = None,
    catalog_root: str | Path | None = None,
) -> BacktestResultArtifact | dict[str, object] | None:
    job = jobs.get_job(job_id, context=context)
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

    jobs.transition_job(job.job_id, "RUNNING", worker_id=worker_image, context=context)
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
    if strategy_spec_payload is not None or catalog_dataset is not None or artifact_store is not None:
        if context is None or artifact_store is None or strategy_spec_payload is None or catalog_dataset is None:
            raise ValueError("strategy-spec replay requires context, artifact_store, strategy_spec_payload, and catalog_dataset")
        evidence = run_strategy_spec_catalog_replay(
            strategy_spec_payload=strategy_spec_payload,
            dataset=catalog_dataset,
            context=context,
            catalog_root=catalog_root,
        )
        record = artifact_store.put_json(
            context=context,
            artifact_type="backtest_result",
            artifact_id=f"{job.job_id}_strategy_spec_replay",
            payload={**evidence, "backtest_job_id": job.job_id, "worker_image": worker_image},
            metadata={
                "job_id": job.job_id,
                "engine_mode": str(evidence["engine_mode"]),
                "dataset_id": str(evidence["dataset_id"]),
            },
        )
        artifact_refs = {"strategy_spec_replay": record.artifact_ref}
        jobs.transition_job(job.job_id, "SUCCEEDED", worker_id=worker_image, result_artifact_refs=artifact_refs, context=context)
        events.append_event(
            job_id=job.job_id,
            actor_type="worker",
            actor_id=worker_image,
            stage="SUCCEEDED",
            level="INFO",
            message="StrategySpec catalog replay worker succeeded",
            progress_pct=100.0,
            metadata={"worker_image": worker_image, "artifact_refs": artifact_refs, "dataset_id": catalog_dataset.dataset_id},
        )
        return {**evidence, "artifact_refs": artifact_refs, "backtest_job_id": job.job_id}

    result = run_backtest_fixture(
        backtest_job_id=job.job_id,
        strategy_spec_version=job.strategy_spec_version_id,
        adapter_id=job.adapter_profile_id,
        instrument_id=job.instrument_id,
        compile_hash=job.compile_hash,
        worker_image=worker_image,
    )
    jobs.transition_job(job.job_id, "SUCCEEDED", worker_id=worker_image, result_artifact_refs=result.artifact_refs, context=context)
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
