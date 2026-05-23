from __future__ import annotations

from .models import AiDraftResult
from .provider import AdvisoryDraftProvider, DraftProviderProtocol, RecordedAiDraftStore


class AiBuilderService:
    def __init__(
        self,
        *,
        provider: DraftProviderProtocol | None = None,
        store: RecordedAiDraftStore | None = None,
    ) -> None:
        self._provider = provider or AdvisoryDraftProvider()
        self._store = store or RecordedAiDraftStore()

    def generate_draft(
        self,
        prompt: str,
        *,
        force_invalid: bool = False,
        include_forbidden_execution: bool = False,
        ai_thread_id: str = "anonymous_thread",
    ) -> AiDraftResult:
        lowered = prompt.lower()
        if include_forbidden_execution or "submit order" in lowered or "submit orders" in lowered:
            raise ValueError("forbidden execution request")

        spec = self._provider.draft_spec(prompt)
        if "submit_order" in spec or spec.get("output") not in {None, "signal_preview_only"}:
            raise ValueError("forbidden execution request")

        if force_invalid:
            spec.pop("risk", None)
            result = AiDraftResult(
                spec=spec,
                accepted=False,
                validation_errors=["risk block missing"],
                explanation="Draft rejected until required Builder risk block is present.",
            )
        else:
            result = AiDraftResult(
                spec=spec,
                accepted=True,
                validation_errors=[],
                explanation="Draft generated in advisory mode and kept in Draft lifecycle stage.",
            )
        self._store.save(
            {
                "ai_thread_id": ai_thread_id,
                "mode": "advisory_only",
                "stage": "draft",
                "accepted": result.accepted,
                "spec": result.spec,
            }
        )
        return result
