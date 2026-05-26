from __future__ import annotations

from pathlib import Path

from packages.artifact_store import LocalJsonArtifactStore
from packages.auth import UserProjectContext
from packages.backtest_jobs.service import BacktestJobService
from packages.backtest_runner import STRATEGY_SPEC_CATALOG_REPLAY_MODE, run_strategy_spec_synthetic_catalog_smoke
from packages.catalog_datasets import CatalogDataset, CatalogDatasetRegistryService
from packages.runtime_events.service import RuntimeEventService
from packages.strategy_compiler.compiler import compile_strategy_spec
from packages.strategy_spec.models import StrategySpec
from packages.strategy_spec.repository import InMemoryStrategyRepository
from services.api.routes.backtest_jobs import create_backtest_job_payload
from services.api.routes.backtest_execution import run_backtest_job_payload
from tests.strategy_spec.test_schema_valid import make_valid_spec


def _context() -> UserProjectContext:
    return UserProjectContext(user_id="user_123", project_id="project_alpha")


def _strategy_spec_payload() -> dict[str, object]:
    spec = make_valid_spec()
    spec["data_range"] = {
        "start": "2024-01-01",
        "end": "2024-03-01",
    }
    return spec


def _date_range(spec: dict[str, object]) -> str:
    data_range = spec["data_range"]
    assert isinstance(data_range, dict)
    return f"{data_range['start']}:{data_range['end']}"


def _registry_with_dataset(tmp_path: Path, context: UserProjectContext, spec: dict[str, object]) -> CatalogDatasetRegistryService:
    registry = CatalogDatasetRegistryService(catalog_root=tmp_path)
    registry.register_dataset(
        CatalogDataset(
            dataset_id="ds_btcusdt_perp_2024_q1",
            user_id=context.user_id,
            project_id=context.project_id,
            adapter_id=str(spec["adapter_id"]),
            instrument_id=str(spec["instrument_id"]),
            data_type="quote_ticks",
            timeframe="1m",
            market_type="crypto_perp",
            date_range=_date_range(spec),
            catalog_path=(tmp_path / "catalogs" / "ds_btcusdt_perp_2024_q1").as_posix(),
        )
    )
    return registry


def _repository_with_strategy(context: UserProjectContext, spec: dict[str, object]) -> tuple[InMemoryStrategyRepository, str]:
    repository = InMemoryStrategyRepository()
    record = repository.save(StrategySpec.model_validate(spec), context=context)
    return repository, str(record["strategy_version_id"])


def _create_job(
    *,
    jobs: BacktestJobService,
    registry: CatalogDatasetRegistryService,
    context: UserProjectContext,
    strategy_version_id: str,
    spec: dict[str, object],
) -> str:
    compile_hash = compile_strategy_spec(spec, profile="backtest").compile_hash
    response = create_backtest_job_payload(
        jobs,
        {
            "strategy_version_id": strategy_version_id,
            "adapter_profile_id": spec["adapter_id"],
            "instrument_id": spec["instrument_id"],
            "validation_report_id": "validation_001",
            "compile_hash": compile_hash,
            "compile_artifact_id": "compile_001",
            "created_by": "operator_001",
            "data_range": _date_range(spec),
            "data_type": "quote_ticks",
            "timeframe": "1m",
            "market_type": "crypto_perp",
            "dataset_id": "ds_btcusdt_perp_2024_q1",
        },
        context=context,
        dataset_registry=registry,
        strict_scope=True,
    )
    assert response.status_code == 201
    return str(response.json()["job_id"])


def test_run_backtest_job_executes_backtestnode_catalog_replay_and_persists_artifact(tmp_path: Path) -> None:
    context = _context()
    spec = _strategy_spec_payload()
    registry = _registry_with_dataset(tmp_path, context, spec)
    repository, strategy_version_id = _repository_with_strategy(context, spec)
    dataset = registry.get_dataset("ds_btcusdt_perp_2024_q1")
    run_strategy_spec_synthetic_catalog_smoke(
        strategy_spec_payload=spec,
        dataset=dataset,
        context=context,
        catalog_root=tmp_path,
    )
    jobs = BacktestJobService()
    events = RuntimeEventService()
    artifacts = LocalJsonArtifactStore(root=tmp_path / "artifacts")
    job_id = _create_job(
        jobs=jobs,
        registry=registry,
        context=context,
        strategy_version_id=strategy_version_id,
        spec=spec,
    )

    response = run_backtest_job_payload(
        jobs,
        job_id,
        events=events,
        strategy_repository=repository,
        dataset_registry=registry,
        artifact_store=artifacts,
        context=context,
        strict_scope=True,
        worker_image="nautilus-builder-worker:test",
    )

    body = response.json()
    assert response.status_code == 200
    assert body["job"]["status"] == "succeeded"
    assert body["job"]["stage"] == "SUCCEEDED"
    assert body["job"]["worker_id"] == "nautilus-builder-worker:test"
    artifact_ref = body["job"]["result_artifact_refs"]["strategy_spec_replay"]
    stored = artifacts.get_json(context=context, artifact_ref=artifact_ref)
    assert stored.payload["engine_mode"] == STRATEGY_SPEC_CATALOG_REPLAY_MODE
    assert stored.payload["dataset_source"] == "user_catalog"
    assert stored.payload["catalog_backed"] is True
    assert stored.payload["strategy_logic_evaluated"] is True
    assert stored.payload["order_intent_count"] == 0
    assert stored.payload["orders"] == 0
    assert stored.payload["positions"] == 0
    assert stored.payload["execution_authority"] is False
    assert stored.payload["credentials_used"] is False
    assert [event["stage"] for event in body["events"]] == ["RUNNING", "SUCCEEDED"]


def test_run_backtest_job_returns_typed_422_when_artifact_store_is_missing(tmp_path: Path) -> None:
    context = _context()
    spec = _strategy_spec_payload()
    registry = _registry_with_dataset(tmp_path, context, spec)
    repository, strategy_version_id = _repository_with_strategy(context, spec)
    jobs = BacktestJobService()
    events = RuntimeEventService()
    job_id = _create_job(
        jobs=jobs,
        registry=registry,
        context=context,
        strategy_version_id=strategy_version_id,
        spec=spec,
    )

    response = run_backtest_job_payload(
        jobs,
        job_id,
        events=events,
        strategy_repository=repository,
        dataset_registry=registry,
        artifact_store=None,
        context=context,
        strict_scope=True,
    )

    assert response.status_code == 422
    assert response.json()["error"] == "invalid_backtest_job_run_request"
    assert "artifact store is required" in response.json()["details"]


def test_run_backtest_job_denies_cross_project_context() -> None:
    jobs = BacktestJobService()
    events = RuntimeEventService()
    job = jobs.create_job(
        {
            "strategy_spec_version_id": "strategy_001_v001",
            "adapter_profile_id": "BINANCE_PERP",
            "instrument_id": "BTCUSDT-PERP",
            "compile_hash": "a" * 64,
            "validation_report_id": "validation_001",
            "user_id": "user_123",
            "project_id": "project_alpha",
        }
    )

    response = run_backtest_job_payload(
        jobs,
        job.job_id,
        events=events,
        strategy_repository=InMemoryStrategyRepository(),
        dataset_registry=None,
        artifact_store=None,
        context=UserProjectContext(user_id="user_456", project_id="project_beta"),
        strict_scope=True,
    )

    assert response.status_code == 403
    assert response.json()["error"] == "forbidden"
    assert events.replay_events(job.job_id) == []


def test_run_backtest_job_honors_cancel_requested_without_requiring_catalog_dependencies() -> None:
    context = _context()
    jobs = BacktestJobService()
    events = RuntimeEventService()
    job = jobs.create_job(
        {
            "strategy_spec_version_id": "strategy_001_v001",
            "adapter_profile_id": "BINANCE_PERP",
            "instrument_id": "BTCUSDT-PERP",
            "compile_hash": "a" * 64,
            "validation_report_id": "validation_001",
            "user_id": context.user_id,
            "project_id": context.project_id,
        }
    )
    jobs.request_cancel(job.job_id, context=context)

    response = run_backtest_job_payload(
        jobs,
        job.job_id,
        events=events,
        strategy_repository=InMemoryStrategyRepository(),
        dataset_registry=None,
        artifact_store=None,
        context=context,
        strict_scope=True,
    )

    assert response.status_code == 200
    assert response.json()["job"]["status"] == "cancel_requested"
    assert response.json()["result"] is None
    assert events.replay_events(job.job_id)[0].stage == "CANCEL_REQUESTED"


def test_run_backtest_job_marks_job_failed_when_catalog_replay_rejects_dataset(tmp_path: Path) -> None:
    context = _context()
    spec = _strategy_spec_payload()
    registry = _registry_with_dataset(tmp_path, context, spec)
    repository, strategy_version_id = _repository_with_strategy(context, spec)
    # Create the selected catalog directory but intentionally do not seed quote ticks.
    Path(registry.get_dataset("ds_btcusdt_perp_2024_q1").catalog_path).mkdir(parents=True)
    jobs = BacktestJobService()
    events = RuntimeEventService()
    artifacts = LocalJsonArtifactStore(root=tmp_path / "artifacts")
    job_id = _create_job(
        jobs=jobs,
        registry=registry,
        context=context,
        strategy_version_id=strategy_version_id,
        spec=spec,
    )

    response = run_backtest_job_payload(
        jobs,
        job_id,
        events=events,
        strategy_repository=repository,
        dataset_registry=registry,
        artifact_store=artifacts,
        context=context,
        strict_scope=True,
        worker_image="nautilus-builder-worker:test",
    )

    assert response.status_code == 422
    assert "user catalog has no matching quote_ticks" in response.json()["details"]
    assert jobs.get_job(job_id, context=context).stage == "FAILED"
    assert [event.stage for event in events.replay_events(job_id)] == ["RUNNING", "FAILED"]
