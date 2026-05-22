from __future__ import annotations

from packages.ai_builder.service import AiBuilderService


def generate_ai_draft_payload(prompt: str) -> dict[str, object]:
    service = AiBuilderService()
    return service.generate_draft(prompt).model_dump(mode="json")
