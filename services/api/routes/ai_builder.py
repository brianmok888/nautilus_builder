from __future__ import annotations

from packages.ai_builder.service import AiBuilderService


def generate_ai_draft_payload(prompt: str) -> dict[str, object]:
    service = AiBuilderService()
    return service.generate_draft(prompt).model_dump(mode="json")


def apply_ai_draft_payload(payload: dict[str, object]) -> dict[str, object]:
    service = AiBuilderService()
    return service.apply_draft_to_strategy(
        str(payload.get("prompt", "")),
        ai_thread_id=str(payload.get("ai_thread_id", "")),
        improvement_cycle_id=str(payload.get("improvement_cycle_id", "")),
        strategy_lineage_id=str(payload.get("strategy_lineage_id", "")),
        strategy_version_id=str(payload.get("strategy_version_id", "")),
    )
