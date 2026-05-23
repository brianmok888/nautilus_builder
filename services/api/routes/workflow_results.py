from __future__ import annotations

from packages.workflow_spine import InMemoryWorkflowRepository
from services.api.router import ApiResponse


def workflow_result_payload(repository: InMemoryWorkflowRepository, result_id: str) -> ApiResponse:
    result = repository.result(result_id)
    if result is None:
        return ApiResponse({"error": "result_not_found", "result_id": result_id}, status_code=404)
    return ApiResponse(result.model_dump(mode="json"))


def workflow_result_suggestions_payload(repository: InMemoryWorkflowRepository, result_id: str) -> ApiResponse:
    suggestions = repository.suggestions_for_result(result_id)
    return ApiResponse([suggestion.model_dump(mode="json") for suggestion in suggestions])
