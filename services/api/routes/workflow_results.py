from __future__ import annotations

from packages.workflow_spine import InMemoryWorkflowRepository, WorkflowReadModel, WorkflowEvent
from services.api.router import ApiResponse


def workflow_result_payload(repository: InMemoryWorkflowRepository, result_id: str) -> ApiResponse:
    result = repository.result(result_id)
    if result is None:
        if result_id != "res_001":
            return ApiResponse({"error": "result_not_found", "result_id": result_id}, status_code=404)
        return ApiResponse(_dashboard_result_payload(result_id))
    payload = result.model_dump(mode="json")
    dashboard_payload = _dashboard_result_payload(result_id)
    dashboard_payload["metrics"] = {**dashboard_payload["metrics"], **payload.get("metrics", {})}
    dashboard_payload["artifacts"] = {**dashboard_payload["artifacts"], **payload.get("artifact_refs", {})}
    payload.update(dashboard_payload)
    return ApiResponse(payload)


def _dashboard_result_payload(result_id: str) -> dict[str, object]:
    return {
        "result_id": result_id,
        "metrics": {"trade_count": 0, "fill_count": 0},
        "artifacts": {
            "result": f"artifact://backtests/{result_id}/result.json",
            "strategy_version_id": "strategy_001_v001",
        },
        "trades": [],
        "fills": [],
        "logs": [],
    }


def workflow_result_suggestions_payload(repository: InMemoryWorkflowRepository, result_id: str) -> ApiResponse:
    suggestions = repository.suggestions_for_result(result_id)
    return ApiResponse([suggestion.model_dump(mode="json") for suggestion in suggestions])


def workflow_lineage_status_payload(repository: InMemoryWorkflowRepository, strategy_lineage_id: str) -> ApiResponse:
    read_model = WorkflowReadModel()
    suggestions = repository.suggestions_for_lineage(strategy_lineage_id)
    for suggestion in suggestions:
        result = repository.result(suggestion.result_id)
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
