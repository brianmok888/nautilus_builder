from __future__ import annotations

from packages.execution_lane import ExecutionLaneService, default_execution_lane_service
from services.api.router import ApiResponse


def execution_lane_status_payload(
    *,
    service: ExecutionLaneService | None = None,
    runtime_profile_id: str | None = None,
) -> dict[str, object]:
    service = service or default_execution_lane_service()
    return service.snapshot(runtime_profile_id=runtime_profile_id)


def register_execution_lane_profile_payload(
    payload: dict[str, object],
    *,
    service: ExecutionLaneService | None = None,
) -> ApiResponse:
    service = service or default_execution_lane_service()
    try:
        profile = service.register_profile(payload)
    except ValueError as exc:
        return ApiResponse({"error": "invalid_execution_lane_profile", "details": str(exc)}, status_code=422)
    return ApiResponse(profile.model_dump(mode="json"), status_code=201)


def enqueue_execution_lane_command_payload(
    payload: dict[str, object],
    *,
    service: ExecutionLaneService | None = None,
) -> ApiResponse:
    service = service or default_execution_lane_service()
    try:
        command = service.enqueue_command(payload)
    except ValueError as exc:
        return ApiResponse({"error": "invalid_execution_lane_command", "details": str(exc)}, status_code=422)
    return ApiResponse(command.model_dump(mode="json"), status_code=201)
