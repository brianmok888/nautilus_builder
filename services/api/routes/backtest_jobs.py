from __future__ import annotations

from packages.backtest_jobs.service import BacktestJobService
from packages.runtime_events.redis_stream import RedisRuntimeEventStream
from services.api.router import ApiResponse


def create_backtest_job_payload(service: BacktestJobService, payload: dict[str, object]) -> ApiResponse:
    job = service.create_job(
        {
            "strategy_spec_version": str(payload["strategy_version_id"]),
            "adapter_id": str(payload["adapter_profile_id"]),
            "instrument_id": str(payload["instrument_id"]),
            "compile_hash": str(payload["compile_artifact_id"]),
            "validation_report_id": str(payload["validation_report_id"]),
        }
    )
    return ApiResponse(
        {
            "job_id": job.job_id,
            "backend_job_id": job.job_id,
            "status": _status_from_stage(job.stage),
            "stage": job.stage,
            "mode": "backend_owned",
        },
        status_code=201,
    )


def backtest_job_payload(service: BacktestJobService, job_id: str) -> ApiResponse:
    try:
        job = service.get_job(job_id)
    except KeyError:
        return ApiResponse({"error": "backtest_job_not_found", "job_id": job_id}, status_code=404)
    return ApiResponse(
        {
            "job_id": job.job_id,
            "status": _status_from_stage(job.stage),
            "stage": job.stage,
            "cancel_requested": job.cancel_requested,
            "mode": "backend_owned",
        }
    )


def cancel_backtest_job_payload(service: BacktestJobService, job_id: str) -> ApiResponse:
    try:
        job = service.request_cancel(job_id)
    except KeyError:
        return ApiResponse({"error": "backtest_job_not_found", "job_id": job_id}, status_code=404)
    return ApiResponse(
        {
            "job_id": job.job_id,
            "status": _status_from_stage(job.stage),
            "stage": job.stage,
            "cancel_requested": job.cancel_requested,
        }
    )


def backtest_job_events_payload(job_id: str) -> ApiResponse:
    stream_name = RedisRuntimeEventStream.STREAM_PATTERN.format(job_id=job_id)
    return ApiResponse({"job_id": job_id, "stream_name": stream_name, "status": "observing", "mode": "observational", "events": []})


def _status_from_stage(stage: str) -> str:
    return {
        "CREATED": "queued",
        "CANCEL_REQUESTED": "cancel_requested",
    }.get(stage, stage.lower())
