from __future__ import annotations

import hashlib
import re

from packages.auth import ProjectScopeError, UserProjectContext
from packages.backtest_jobs.service import BacktestJobService
from packages.catalog_datasets import CatalogDatasetRegistryService
from packages.instrument_registry.service import InstrumentRegistryService
from packages.runtime_events.redis_stream import RedisRuntimeEventStream
from services.api.router import ApiResponse

_STRICT_REQUIRED_FIELDS = (
    "strategy_version_id",
    "adapter_profile_id",
    "instrument_id",
    "compile_hash",
    "validation_report_id",
    "data_range",
    "data_type",
    "timeframe",
    "market_type",
    "dataset_id",
)


def create_backtest_job_payload(
    service: BacktestJobService,
    payload: dict[str, object],
    *,
    context: UserProjectContext | None = None,
    dataset_registry: CatalogDatasetRegistryService | None = None,
    strict_scope: bool = False,
) -> ApiResponse:
    if strict_scope and context is None:
        return ApiResponse({"error": "auth_required", "details": "bearer auth context is required"}, status_code=401)

    if strict_scope:
        missing = [field for field in _STRICT_REQUIRED_FIELDS if not str(payload.get(field, "")).strip()]
        if missing:
            return ApiResponse(
                {"error": "invalid_backtest_job_request", "details": f"missing required fields: {', '.join(missing)}"},
                status_code=422,
            )
        compile_hash_error = _compile_hash_error(str(payload.get("compile_hash", "")))
        if compile_hash_error is not None:
            return ApiResponse({"error": "invalid_backtest_job_request", "details": compile_hash_error}, status_code=422)
        if dataset_registry is None:
            return ApiResponse(
                {"error": "invalid_backtest_job_request", "details": "catalog dataset registry is required"},
                status_code=422,
            )
        try:
            InstrumentRegistryService().validate_selection(
                adapter_id=str(payload["adapter_profile_id"]),
                instrument_id=str(payload["instrument_id"]),
                data_type=str(payload["data_type"]),
                timeframe=str(payload["timeframe"]),
                market_type=str(payload["market_type"]),
                date_range=str(payload["data_range"]),
            )
            dataset = dataset_registry.select_dataset(
                context=context,
                dataset_id=str(payload["dataset_id"]),
                adapter_id=str(payload["adapter_profile_id"]),
                instrument_id=str(payload["instrument_id"]),
                data_type=str(payload["data_type"]),
                timeframe=str(payload["timeframe"]),
                market_type=str(payload["market_type"]),
                date_range=str(payload["data_range"]),
                strict_root_policy=True,
            )
        except ProjectScopeError as exc:
            return ApiResponse({"error": "forbidden", "message": str(exc)}, status_code=403)
        except ValueError as exc:
            return ApiResponse({"error": "invalid_backtest_job_request", "details": str(exc)}, status_code=422)

        job_payload = {
            "strategy_spec_version_id": str(payload["strategy_version_id"]),
            "adapter_profile_id": str(payload["adapter_profile_id"]),
            "instrument_id": str(payload["instrument_id"]),
            "compile_hash": str(payload["compile_hash"]),
            "validation_report_id": str(payload["validation_report_id"]),
            "compile_artifact_id": str(payload.get("compile_artifact_id", "")),
            "created_by": str(payload.get("created_by", context.user_id)),
            "data_range": str(payload["data_range"]),
            "user_id": context.user_id,
            "project_id": context.project_id,
            "dataset_id": dataset.dataset_id,
            "catalog_path": dataset.catalog_path,
            "data_type": dataset.data_type,
            "timeframe": dataset.timeframe,
            "market_type": dataset.market_type,
        }
    else:
        required = ("strategy_version_id", "adapter_profile_id", "instrument_id", "validation_report_id")
        missing = [field for field in required if not str(payload.get(field, "")).strip()]
        if not str(payload.get("compile_hash") or payload.get("compile_artifact_id") or "").strip():
            missing.append("compile_hash")
        if missing:
            return ApiResponse(
                {"error": "invalid_backtest_job_request", "details": f"missing required fields: {', '.join(missing)}"},
                status_code=422,
            )
        try:
            compile_hash, compile_artifact_id = _compile_lineage_from_payload(payload, strict_scope=False)
        except ValueError as exc:
            return ApiResponse({"error": "invalid_backtest_job_request", "details": str(exc)}, status_code=422)
        job_payload = {
            "strategy_spec_version_id": str(payload["strategy_version_id"]),
            "adapter_profile_id": str(payload["adapter_profile_id"]),
            "instrument_id": str(payload["instrument_id"]),
            "compile_hash": compile_hash,
            "validation_report_id": str(payload["validation_report_id"]),
            "compile_artifact_id": compile_artifact_id,
            "created_by": str(payload.get("created_by", "builder_api")),
            "data_range": str(payload.get("data_range", "unspecified")),
            "user_id": str(payload.get("user_id", "system")),
            "project_id": str(payload.get("project_id", "default")),
            "dataset_id": str(payload.get("dataset_id", "unspecified")),
            "catalog_path": str(payload.get("catalog_path", "")),
            "data_type": str(payload.get("data_type", "unspecified")),
            "timeframe": str(payload.get("timeframe", "unspecified")),
            "market_type": str(payload.get("market_type", "unspecified")),
        }

    job = service.create_job(job_payload)
    return ApiResponse(_job_response(job, include_backend_id=True), status_code=201)


def backtest_job_payload(
    service: BacktestJobService,
    job_id: str,
    *,
    context: UserProjectContext | None = None,
    user_id: str | None = None,
    project_id: str | None = None,
    strict_scope: bool = False,
) -> ApiResponse:
    try:
        access_context = _access_context(context=context, user_id=user_id, project_id=project_id, strict_scope=strict_scope)
        if strict_scope and access_context is None:
            return ApiResponse({"error": "auth_required", "details": "bearer auth context is required"}, status_code=401)
        job = service.get_job(job_id, context=access_context)
    except KeyError:
        return ApiResponse({"error": "backtest_job_not_found", "job_id": job_id}, status_code=404)
    except ProjectScopeError as exc:
        return ApiResponse({"error": "forbidden", "message": str(exc)}, status_code=403)
    return ApiResponse(_job_response(job))


def cancel_backtest_job_payload(
    service: BacktestJobService,
    job_id: str,
    *,
    context: UserProjectContext | None = None,
    user_id: str | None = None,
    project_id: str | None = None,
    strict_scope: bool = False,
) -> ApiResponse:
    try:
        access_context = _access_context(context=context, user_id=user_id, project_id=project_id, strict_scope=strict_scope)
        if strict_scope and access_context is None:
            return ApiResponse({"error": "auth_required", "details": "bearer auth context is required"}, status_code=401)
        job = service.request_cancel(job_id, context=access_context)
    except KeyError:
        return ApiResponse({"error": "backtest_job_not_found", "job_id": job_id}, status_code=404)
    except ProjectScopeError as exc:
        return ApiResponse({"error": "forbidden", "message": str(exc)}, status_code=403)
    return ApiResponse(_job_response(job))


def backtest_job_events_payload(job_id: str, *, service=None) -> ApiResponse:
    stream_name = RedisRuntimeEventStream.STREAM_PATTERN.format(job_id=job_id)
    events = [] if service is None else [event.model_dump(mode="json") for event in service.replay_events(job_id)]
    return ApiResponse(
        {
            "job_id": job_id,
            "stream_name": stream_name,
            "status": "observing",
            "mode": "observational",
            "events": events,
        }
    )


def _job_response(job, *, include_backend_id: bool = False) -> dict[str, object]:
    payload = {
        "job_id": job.job_id,
        "status": _status_from_stage(job.stage),
        "stage": job.stage,
        "lifecycle_status": job.status,
        "created_by": job.created_by,
        "created_at": job.created_at,
        "updated_at": job.updated_at,
        "strategy_spec_version_id": job.strategy_spec_version_id,
        "adapter_profile_id": job.adapter_profile_id,
        "instrument_id": job.instrument_id,
        "data_range": job.data_range,
        "data_type": job.data_type,
        "timeframe": job.timeframe,
        "market_type": job.market_type,
        "worker_id": job.worker_id,
        "result_artifact_refs": job.result_artifact_refs,
        "event_stream_id": job.event_stream_id,
        "user_id": job.user_id,
        "project_id": job.project_id,
        "dataset_id": job.dataset_id,
        "catalog_path": job.catalog_path,
        "cancel_requested": job.cancel_requested,
        "compile_hash": job.compile_hash,
        "compile_artifact_id": job.compile_artifact_id,
        "mode": "backend_owned",
    }
    if include_backend_id:
        payload["backend_job_id"] = job.job_id
    return payload


def _status_from_stage(stage: str) -> str:
    return {
        "CREATED": "queued",
        "RUNNING": "running",
        "SUCCEEDED": "succeeded",
        "CANCEL_REQUESTED": "cancel_requested",
        "FAILED": "failed",
    }.get(stage, stage.lower())


def _access_context(
    *,
    context: UserProjectContext | None,
    user_id: str | None,
    project_id: str | None,
    strict_scope: bool,
) -> UserProjectContext | None:
    if strict_scope:
        return context
    return _context_from_values(user_id=user_id, project_id=project_id)


def _context_from_values(*, user_id: str | None, project_id: str | None) -> UserProjectContext | None:
    if user_id is None and project_id is None:
        return None
    if not user_id or not project_id:
        raise ProjectScopeError("user_id and project_id are required together for scoped access")
    return UserProjectContext(user_id=user_id, project_id=project_id)


_SHA256_RE = re.compile(r"^[a-fA-F0-9]{64}$")

def _compile_hash_error(value: str) -> str | None:
    if _SHA256_RE.fullmatch(value) is None:
        return "compile_hash must be a 64-character hex sha256 digest"
    return None

def _compile_lineage_from_payload(payload: dict[str, object], *, strict_scope: bool) -> tuple[str, str]:
    compile_hash = str(payload.get("compile_hash") or "").strip()
    compile_artifact_id = str(payload.get("compile_artifact_id") or "").strip()
    if compile_hash:
        error = _compile_hash_error(compile_hash)
        if error is not None:
            raise ValueError(error)
        return compile_hash.lower(), compile_artifact_id
    if strict_scope:
        raise ValueError("compile_hash is required")
    if compile_artifact_id:
        legacy_hash = hashlib.sha256(f"compile_artifact_id:{compile_artifact_id}".encode("utf-8")).hexdigest()
        return legacy_hash, compile_artifact_id
    raise ValueError("compile_hash is required")
