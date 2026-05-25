from __future__ import annotations

import pytest

from packages.artifact_store import LocalJsonArtifactStore
from packages.auth import ProjectScopeError, UserProjectContext
from packages.backtest_jobs.service import BacktestJobService
from packages.backtest_runner import STRATEGY_SPEC_CATALOG_REPLAY_MODE, run_strategy_spec_synthetic_catalog_smoke
from packages.catalog_datasets import CatalogDataset
from packages.runtime_events.service import RuntimeEventService
from services.workers.nautilus_backtest_worker import run_backtest_job
from tests.strategy_spec.test_schema_valid import make_valid_spec


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


def test_worker_can_run_strategy_spec_catalog_replay_and_persist_artifact(tmp_path) -> None:
    spec = make_valid_spec()
    context = UserProjectContext(user_id="user_123", project_id="project_alpha")
    jobs = BacktestJobService()
    events = RuntimeEventService()
    artifacts = LocalJsonArtifactStore(root=tmp_path / "artifacts")
    dataset = CatalogDataset(
        dataset_id="ds_btcusdt_perp_2025",
        user_id=context.user_id,
        project_id=context.project_id,
        adapter_id=spec["adapter_id"],
        instrument_id=spec["instrument_id"],
        data_type="quote_ticks",
        timeframe="1m",
        market_type="crypto_perp",
        date_range=f"{spec['data_range']['start']}:{spec['data_range']['end']}",
        catalog_path=(tmp_path / "catalogs" / "ds_btcusdt_perp_2025").as_posix(),
    )
    run_strategy_spec_synthetic_catalog_smoke(
        strategy_spec_payload=spec,
        dataset=dataset,
        context=context,
        catalog_root=tmp_path,
    )
    job = jobs.create_job(
        {
            "strategy_spec_version": spec["version"],
            "adapter_id": spec["adapter_id"],
            "instrument_id": spec["instrument_id"],
            "compile_hash": "abc123",
            "validation_report_id": "vr_001",
            "user_id": context.user_id,
            "project_id": context.project_id,
            "dataset_id": dataset.dataset_id,
            "catalog_path": dataset.catalog_path,
            "data_range": dataset.date_range,
        }
    )

    result = run_backtest_job(
        job_id=job.job_id,
        jobs=jobs,
        events=events,
        worker_image="nautilus-builder-worker:dev",
        context=context,
        artifact_store=artifacts,
        strategy_spec_payload=spec,
        catalog_dataset=dataset,
        catalog_root=tmp_path,
    )

    assert result is not None
    stored_ref = jobs.get_job(job.job_id).result_artifact_refs["strategy_spec_replay"]
    stored = artifacts.get_json(context=context, artifact_ref=stored_ref)
    assert stored.payload["engine_mode"] == STRATEGY_SPEC_CATALOG_REPLAY_MODE
    assert stored.payload["dataset_id"] == dataset.dataset_id
    assert events.replay_events(job.job_id)[-1].metadata["artifact_refs"]["strategy_spec_replay"] == stored_ref


def test_worker_strategy_spec_replay_requires_catalog_root(tmp_path) -> None:
    spec = make_valid_spec()
    context = UserProjectContext(user_id="user_123", project_id="project_alpha")
    jobs = BacktestJobService()
    events = RuntimeEventService()
    artifacts = LocalJsonArtifactStore(root=tmp_path / "artifacts")
    dataset = CatalogDataset(
        dataset_id="ds_btcusdt_perp_2025",
        user_id=context.user_id,
        project_id=context.project_id,
        adapter_id=spec["adapter_id"],
        instrument_id=spec["instrument_id"],
        data_type="quote_ticks",
        timeframe="1m",
        market_type="crypto_perp",
        date_range=f"{spec['data_range']['start']}:{spec['data_range']['end']}",
        catalog_path=(tmp_path / "catalogs" / "ds_btcusdt_perp_2025").as_posix(),
    )
    job = jobs.create_job(
        {
            "strategy_spec_version": spec["version"],
            "adapter_id": spec["adapter_id"],
            "instrument_id": spec["instrument_id"],
            "compile_hash": "abc123",
            "validation_report_id": "vr_001",
            "user_id": context.user_id,
            "project_id": context.project_id,
            "dataset_id": dataset.dataset_id,
            "catalog_path": dataset.catalog_path,
            "data_range": dataset.date_range,
        }
    )

    with pytest.raises(ValueError, match="catalog_root is required"):
        run_backtest_job(
            job_id=job.job_id,
            jobs=jobs,
            events=events,
            worker_image="nautilus-builder-worker:dev",
            context=context,
            artifact_store=artifacts,
            strategy_spec_payload=spec,
            catalog_dataset=dataset,
        )


def test_worker_rejects_context_outside_job_scope() -> None:
    jobs = BacktestJobService()
    events = RuntimeEventService()
    job = jobs.create_job(
        {
            "strategy_spec_version": "0.1.0-draft.1",
            "adapter_id": "BINANCE_PERP",
            "instrument_id": "BTCUSDT-PERP",
            "compile_hash": "abc123",
            "validation_report_id": "vr_001",
            "user_id": "user_123",
            "project_id": "project_alpha",
        }
    )
    intruder = UserProjectContext(user_id="user_123", project_id="project_beta")

    with pytest.raises(ProjectScopeError, match="outside user/project scope"):
        run_backtest_job(
            job_id=job.job_id,
            jobs=jobs,
            events=events,
            worker_image="nautilus-builder-worker:dev",
            context=intruder,
        )
