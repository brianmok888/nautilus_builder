from __future__ import annotations

from typing import Any

from packages.artifact_store import LocalJsonArtifactStore
from packages.auth import ProjectScopeError, UserProjectContext
from packages.backtest_jobs.service import BacktestJobService
from packages.catalog_datasets import CatalogDatasetRegistryService
from packages.runtime_events.service import RuntimeEventService
from packages.strategy_compiler.compiler import compile_strategy_spec
from packages.strategy_spec.models import StrategySpec
from packages.strategy_spec.repository import InMemoryStrategyRepository
from services.api.router import ApiResponse
from services.api.routes.backtest_jobs import backtest_job_payload
from services.api.routes.runtime_events import replay_runtime_events_payload
from services.workers.nautilus_backtest_worker import run_backtest_job

_DEFAULT_WORKER_IMAGE = "nautilus-builder-backtest-worker:local"


def run_backtest_job_payload(
    service: BacktestJobService,
    job_id: str,
    *,
    events: RuntimeEventService,
    strategy_repository: InMemoryStrategyRepository,
    dataset_registry: CatalogDatasetRegistryService | None,
    artifact_store: LocalJsonArtifactStore | None,
    context: UserProjectContext | None = None,
    user_id: str | None = None,
    project_id: str | None = None,
    strict_scope: bool = False,
    worker_image: str = _DEFAULT_WORKER_IMAGE,
) -> ApiResponse:
    """Run a queued backtest job through the backend-owned Nautilus worker path.

    This is a local/dev synchronous trigger around the same worker function used by
    dedicated workers. It keeps worker/catalog/artifact authority in the backend;
    the browser can only request a scoped job transition.
    """

    try:
        access_context = _access_context(
            context=context,
            user_id=user_id,
            project_id=project_id,
            strict_scope=strict_scope,
        )
    except ProjectScopeError as exc:
        return ApiResponse({"error": "forbidden", "message": str(exc)}, status_code=403)
    if strict_scope and access_context is None:
        return ApiResponse({"error": "auth_required", "details": "bearer auth context is required"}, status_code=401)

    try:
        job = service.get_job(job_id, context=access_context)
    except KeyError:
        return ApiResponse({"error": "backtest_job_not_found", "job_id": job_id}, status_code=404)
    except ProjectScopeError as exc:
        return ApiResponse({"error": "forbidden", "message": str(exc)}, status_code=403)

    if job.cancel_requested:
        result = run_backtest_job(
            job_id=job.job_id,
            jobs=service,
            events=events,
            worker_image=worker_image,
            context=access_context,
        )
        return ApiResponse(_execution_response(service, job.job_id, events, result, context=access_context))

    dependency_error = _dependency_error(dataset_registry=dataset_registry, artifact_store=artifact_store)
    if dependency_error is not None:
        return dependency_error

    assert dataset_registry is not None
    assert artifact_store is not None

    try:
        strategy_spec = _strategy_spec_for_version(
            strategy_repository,
            job.strategy_spec_version_id,
            context=access_context,
        )
        compile_hash = compile_strategy_spec(strategy_spec.model_dump(mode="json"), profile="backtest").compile_hash
        if job.compile_hash.lower() != compile_hash:
            return ApiResponse(
                {
                    "error": "invalid_backtest_job_run_request",
                    "details": "job compile_hash does not match stored StrategySpec backtest compile hash",
                    "expected_compile_hash": compile_hash,
                    "job_compile_hash": job.compile_hash,
                },
                status_code=422,
            )
        dataset = dataset_registry.select_dataset(
            context=_require_context(access_context),
            dataset_id=job.dataset_id,
            adapter_id=job.adapter_profile_id,
            instrument_id=job.instrument_id,
            data_type=job.data_type,
            timeframe=job.timeframe,
            market_type=job.market_type,
            date_range=job.data_range,
            strict_root_policy=True,
        )
        result = run_backtest_job(
            job_id=job.job_id,
            jobs=service,
            events=events,
            worker_image=worker_image,
            context=access_context,
            artifact_store=artifact_store,
            strategy_spec_payload=strategy_spec.model_dump(mode="json"),
            catalog_dataset=dataset,
            catalog_root=dataset_registry.catalog_root,
        )
    except ProjectScopeError as exc:
        return ApiResponse({"error": "forbidden", "message": str(exc)}, status_code=403)
    except ValueError as exc:
        _record_run_failure_if_started(
            service,
            job.job_id,
            events,
            worker_image=worker_image,
            error=str(exc),
            context=access_context,
        )
        return ApiResponse(
            {"error": "invalid_backtest_job_run_request", "details": str(exc)},
            status_code=422,
        )

    return ApiResponse(_execution_response(service, job.job_id, events, result, context=access_context))


def _record_run_failure_if_started(
    service: BacktestJobService,
    job_id: str,
    events: RuntimeEventService,
    *,
    worker_image: str,
    error: str,
    context: UserProjectContext | None,
) -> None:
    try:
        current = service.get_job(job_id, context=context)
    except (KeyError, ProjectScopeError):
        return
    if current.stage != "RUNNING":
        return
    service.transition_job(job_id, "FAILED", worker_id=worker_image, context=context)
    events.append_event(
        job_id=job_id,
        actor_type="worker",
        actor_id=worker_image,
        stage="FAILED",
        level="ERROR",
        message="Backtest worker failed",
        progress_pct=100.0,
        metadata={"worker_image": worker_image, "error": error},
    )


def _execution_response(
    service: BacktestJobService,
    job_id: str,
    events: RuntimeEventService,
    result: object,
    *,
    context: UserProjectContext | None,
) -> dict[str, object]:
    job_response = backtest_job_payload(service, job_id, context=context, strict_scope=context is not None).json()
    return {
        "mode": "backend_owned_backtestnode",
        "job": job_response,
        "result": _json_result(result),
        "events": replay_runtime_events_payload(service=events, job_id=job_id),
    }


def _json_result(result: object) -> object:
    if result is None:
        return None
    if hasattr(result, "model_dump"):
        return result.model_dump(mode="json")  # type: ignore[no-any-return, attr-defined]
    if isinstance(result, dict):
        return result
    return {"result": str(result)}


def _dependency_error(
    *,
    dataset_registry: CatalogDatasetRegistryService | None,
    artifact_store: LocalJsonArtifactStore | None,
) -> ApiResponse | None:
    if artifact_store is None:
        return ApiResponse(
            {"error": "invalid_backtest_job_run_request", "details": "artifact store is required"},
            status_code=422,
        )
    if dataset_registry is None:
        return ApiResponse(
            {"error": "invalid_backtest_job_run_request", "details": "catalog dataset registry is required"},
            status_code=422,
        )
    if not dataset_registry.has_root_policy:
        return ApiResponse(
            {"error": "invalid_backtest_job_run_request", "details": "catalog_root is required for backtest execution"},
            status_code=422,
        )
    return None


def _strategy_spec_for_version(
    repository: InMemoryStrategyRepository,
    strategy_version_id: str,
    *,
    context: UserProjectContext | None,
) -> StrategySpec:
    spec = repository.spec_for_version(strategy_version_id, context=context)
    if spec is None:
        raise ValueError(f"strategy version not found: {strategy_version_id}")
    return spec


def _access_context(
    *,
    context: UserProjectContext | None,
    user_id: str | None,
    project_id: str | None,
    strict_scope: bool,
) -> UserProjectContext | None:
    if strict_scope:
        return context
    if context is not None:
        return context
    if user_id is None and project_id is None:
        return None
    if not user_id or not project_id:
        raise ProjectScopeError("user_id and project_id are required together for scoped access")
    return UserProjectContext(user_id=user_id, project_id=project_id)


def _require_context(context: UserProjectContext | None) -> UserProjectContext:
    if context is None:
        raise ValueError("user/project context is required for catalog-backed backtest execution")
    return context
