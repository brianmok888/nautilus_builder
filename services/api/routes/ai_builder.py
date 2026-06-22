from __future__ import annotations

from packages.ai_builder.service import AiBuilderService
from services.api.router import ApiResponse


def generate_ai_draft_payload(prompt: str, *, service: AiBuilderService | None = None) -> dict[str, object]:
    service = service or AiBuilderService()
    return service.generate_draft(prompt).model_dump(mode="json")


def apply_ai_draft_payload(
    payload: dict[str, object],
    *,
    service: AiBuilderService | None = None,
) -> ApiResponse:
    service = service or AiBuilderService()
    try:
        spec = payload.get("spec")
        if spec is not None and not isinstance(spec, dict):
            raise ValueError("spec must be an object when provided")
        record = service.apply_draft_to_strategy(
            str(payload.get("prompt", "")),
            ai_thread_id=str(payload.get("ai_thread_id", "")),
            improvement_cycle_id=str(payload.get("improvement_cycle_id", "")),
            strategy_lineage_id=str(payload.get("strategy_lineage_id", "")),
            strategy_version_id=str(payload.get("strategy_version_id", "")),
            spec=spec,
        )
    except ValueError as exc:
        return ApiResponse({"error": "invalid_ai_apply_request", "details": str(exc)}, status_code=422)
    return ApiResponse(record)
