from __future__ import annotations

from packages.auth import ProjectScopeError, UserProjectContext
from packages.workflow_spine import InMemoryWorkflowRepository, WorkflowReadModel, WorkflowEvent
from services.api.router import ApiResponse


def workflow_result_payload(
    repository: InMemoryWorkflowRepository,
    result_id: str,
    *,
    context: UserProjectContext | None = None,
    allow_fixture_fallback: bool = True,
) -> ApiResponse:
    try:
        result = repository.result(result_id, context=context)
    except ProjectScopeError as exc:
        return ApiResponse({"error": "forbidden", "message": str(exc)}, status_code=403)
    if result is None:
        if result_id != "res_001" or not allow_fixture_fallback:
            return ApiResponse({"error": "result_not_found", "result_id": result_id}, status_code=404)
        return ApiResponse(_dashboard_result_payload(result_id, fixture=True))
    payload = result.model_dump(mode="json")
    dashboard_payload = _dashboard_result_payload(result_id, fixture=False)
    dashboard_payload["metrics"] = {**dashboard_payload["metrics"], **payload.get("metrics", {})}
    dashboard_payload["artifacts"] = {**dashboard_payload["artifacts"], **payload.get("artifact_refs", {})}
    payload.update(dashboard_payload)
    return ApiResponse(payload)


def _dashboard_result_payload(result_id: str, *, fixture: bool) -> dict[str, object]:
    result_ref = (
        f"fixture://backtests/{result_id}/result.json"
        if fixture
        else f"artifact://builder/results/{result_id}/result.json"
    )
    return {
        "result_id": result_id,
        "evidence_mode": "fixture_dev_only" if fixture else "repository_result",
        "fixture_evidence_only": fixture,
        "metrics": {"trade_count": 0, "fill_count": 0},
        "artifacts": {
            "result": result_ref,
            "strategy_version_id": "strategy_001_v001",
            "evidence_mode": "fixture_dev_only" if fixture else "repository_result",
        },
        "trades": [],
        "fills": [],
        "logs": [],
    }


def workflow_result_suggestions_payload(
    repository: InMemoryWorkflowRepository,
    result_id: str,
    *,
    context: UserProjectContext | None = None,
) -> ApiResponse:
    try:
        suggestions = repository.suggestions_for_result(result_id, context=context)
    except ProjectScopeError as exc:
        return ApiResponse({"error": "forbidden", "message": str(exc)}, status_code=403)
    return ApiResponse([suggestion.model_dump(mode="json") for suggestion in suggestions])


def workflow_lineage_status_payload(
    repository: InMemoryWorkflowRepository,
    strategy_lineage_id: str,
    *,
    context: UserProjectContext | None = None,
) -> ApiResponse:
    read_model = WorkflowReadModel()
    try:
        suggestions = repository.suggestions_for_lineage(strategy_lineage_id, context=context)
    except ProjectScopeError as exc:
        return ApiResponse({"error": "forbidden", "message": str(exc)}, status_code=403)
    for suggestion in suggestions:
        try:
            result = repository.result(suggestion.result_id, context=context)
        except ProjectScopeError as exc:
            return ApiResponse({"error": "forbidden", "message": str(exc)}, status_code=403)
        if result is not None:
            read_model.apply(
                WorkflowEvent(
                    event="result.completed",
                    project_id=result.project_id,
                    strategy_lineage_id=result.strategy_lineage_id,
                    strategy_version_id=result.strategy_version_id,
                    test_job_id=result.test_job_id,
                    result_id=result.result_id,
                )
            )
        read_model.apply(
            WorkflowEvent(
                event="suggestion.created",
                project_id=suggestion.project_id,
                strategy_lineage_id=suggestion.strategy_lineage_id,
                strategy_version_id=suggestion.strategy_version_id,
                result_id=suggestion.result_id,
                ai_thread_id=suggestion.ai_thread_id,
                improvement_cycle_id=suggestion.improvement_cycle_id,
            )
        )
    try:
        return ApiResponse(read_model.lineage_status(strategy_lineage_id))
    except KeyError:
        return ApiResponse({"error": "lineage_not_found", "strategy_lineage_id": strategy_lineage_id}, status_code=404)
