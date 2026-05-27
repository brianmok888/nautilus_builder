from __future__ import annotations

from packages.execution_lane import ExecutionLaneService, default_execution_lane_service
from services.workers.execution_lane_worker import run_execution_lane_worker_once, start_execution_lane_paper_session, stop_execution_lane_session
from services.api.router import ApiResponse


def execution_lane_status_payload(
    *,
    service: ExecutionLaneService | None = None,
    runtime_profile_id: str | None = None,
) -> dict[str, object]:
    service = service or default_execution_lane_service()
    return service.snapshot(runtime_profile_id=runtime_profile_id)


def create_execution_lane_credential_slot_payload(
    payload: dict[str, object],
    *,
    service: ExecutionLaneService | None = None,
) -> ApiResponse:
    service = service or default_execution_lane_service()
    try:
        slot = service.create_credential_slot(payload)
    except ValueError as exc:
        return ApiResponse({"error": "invalid_execution_lane_credential_slot", "details": str(exc)}, status_code=422)
    return ApiResponse(slot.model_dump(mode="json"), status_code=201)


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


def execution_lane_runtime_plan_payload(
    *,
    runtime_profile_id: str,
    command_id: str | None = None,
    service: ExecutionLaneService | None = None,
) -> ApiResponse:
    service = service or default_execution_lane_service()
    try:
        plan = service.build_trading_node_runtime_plan(
            runtime_profile_id=runtime_profile_id,
            command_id=command_id,
        )
    except KeyError:
        return ApiResponse({"error": "execution_lane_profile_not_found", "runtime_profile_id": runtime_profile_id}, status_code=404)
    except ValueError as exc:
        return ApiResponse({"error": "invalid_execution_lane_runtime_plan", "details": str(exc)}, status_code=422)
    return ApiResponse(plan.model_dump(mode="json"))


def run_execution_lane_worker_once_payload(
    payload: dict[str, object],
    *,
    service: ExecutionLaneService | None = None,
) -> ApiResponse:
    service = service or default_execution_lane_service()
    runtime_profile_id = str(payload.get("runtime_profile_id", "")).strip()
    worker_id = str(payload.get("worker_id", "execution_lane_web_worker")).strip() or "execution_lane_web_worker"
    if not runtime_profile_id:
        return ApiResponse({"error": "invalid_execution_lane_worker_request", "details": "runtime_profile_id is required"}, status_code=422)
    try:
        report = run_execution_lane_worker_once(
            service=service,
            runtime_profile_id=runtime_profile_id,
            worker_id=worker_id,
        )
    except KeyError as exc:
        return ApiResponse(
            {
                "error": "execution_lane_command_not_available",
                "details": str(exc),
                "runtime_profile_id": runtime_profile_id,
            },
            status_code=409,
        )
    except ValueError as exc:
        return ApiResponse({"error": "invalid_execution_lane_worker_request", "details": str(exc)}, status_code=422)
    return ApiResponse(report.model_dump(mode="json"), status_code=202)


def start_execution_lane_paper_session_payload(
    payload: dict[str, object],
    *,
    service: ExecutionLaneService | None = None,
) -> ApiResponse:
    service = service or default_execution_lane_service()
    runtime_profile_id = str(payload.get("runtime_profile_id", "")).strip()
    command_id = str(payload.get("command_id", "")).strip()
    worker_id = str(payload.get("worker_id", "execution_lane_web_worker")).strip() or "execution_lane_web_worker"
    if not runtime_profile_id or not command_id:
        return ApiResponse(
            {"error": "invalid_execution_lane_session", "details": "runtime_profile_id and command_id are required"},
            status_code=422,
        )
    try:
        session = start_execution_lane_paper_session(
            service=service,
            runtime_profile_id=runtime_profile_id,
            command_id=command_id,
            worker_id=worker_id,
        )
    except KeyError as exc:
        return ApiResponse({"error": "execution_lane_session_not_available", "details": str(exc)}, status_code=404)
    except ValueError as exc:
        return ApiResponse({"error": "invalid_execution_lane_session", "details": str(exc)}, status_code=422)
    return ApiResponse(session.model_dump(mode="json"), status_code=202)


def execution_lane_session_payload(
    *,
    session_id: str,
    service: ExecutionLaneService | None = None,
) -> ApiResponse:
    service = service or default_execution_lane_service()
    try:
        session = service.get_session(session_id)
    except KeyError:
        return ApiResponse({"error": "execution_lane_session_not_found", "session_id": session_id}, status_code=404)
    return ApiResponse(session.model_dump(mode="json"))


def stop_execution_lane_session_payload(
    *,
    session_id: str,
    payload: dict[str, object] | None = None,
    service: ExecutionLaneService | None = None,
) -> ApiResponse:
    service = service or default_execution_lane_service()
    payload = payload or {}
    worker_id = str(payload.get("worker_id", "execution_lane_web_worker")).strip() or "execution_lane_web_worker"
    try:
        session = stop_execution_lane_session(service=service, session_id=session_id, worker_id=worker_id)
    except KeyError:
        return ApiResponse({"error": "execution_lane_session_not_found", "session_id": session_id}, status_code=404)
    except ValueError as exc:
        return ApiResponse({"error": "invalid_execution_lane_session", "details": str(exc)}, status_code=422)
    return ApiResponse(session.model_dump(mode="json"), status_code=202)
