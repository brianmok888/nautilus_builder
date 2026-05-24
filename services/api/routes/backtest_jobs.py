from __future__ import annotations

from packages.backtest_jobs.service import BacktestJobService
from packages.runtime_events.redis_stream import RedisRuntimeEventStream
from services.api.router import ApiResponse


def create_backtest_job_payload(service: BacktestJobService, payload: dict[str, object]) -> ApiResponse:
    job = service.create_job(
        {
            "strategy_spec_version_id": str(payload["strategy_version_id"]),
            "adapter_profile_id": str(payload["adapter_profile_id"]),
            "instrument_id": str(payload["instrument_id"]),
            "compile_hash": str(payload["compile_artifact_id"]),
            "validation_report_id": str(payload["validation_report_id"]),
            "created_by": str(payload.get("created_by", "builder_api")),
            "data_range": str(payload.get("data_range", "unspecified")),
        }
    )
    return ApiResponse(_job_response(job, include_backend_id=True), status_code=201)


def backtest_job_payload(service: BacktestJobService, job_id: str) -> ApiResponse:
    try:
        job = service.get_job(job_id)
    except KeyError:
        return ApiResponse({"error": "backtest_job_not_found", "job_id": job_id}, status_code=404)
    return ApiResponse(_job_response(job))


def cancel_backtest_job_payload(service: BacktestJobService, job_id: str) -> ApiResponse:
    try:
        job = service.request_cancel(job_id)
    except KeyError:
        return ApiResponse({"error": "backtest_job_not_found", "job_id": job_id}, status_code=404)
    return ApiResponse(_job_response(job))


def backtest_job_events_payload(job_id: str) -> ApiResponse:
    stream_name = RedisRuntimeEventStream.STREAM_PATTERN.format(job_id=job_id)
    return ApiResponse(
        {
            "job_id": job_id,
            "stream_name": stream_name,
            "status": "observing",
            "mode": "observational",
            "events": [],
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
        "worker_id": job.worker_id,
        "result_artifact_refs": job.result_artifact_refs,
        "event_stream_id": job.event_stream_id,
        "cancel_requested": job.cancel_requested,
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
    }.get(stage, stage.lower())
