from __future__ import annotations

import pytest

from packages.ai_builder.service import AiBuilderService
from packages.ai_builder.provider import AdvisoryDraftProvider, RecordedAiDraftStore


def test_ai_output_becomes_draft_strategy_spec_only() -> None:
    service = AiBuilderService()

    result = service.generate_draft("Create an EMA/RSI pullback strategy")

    assert result.spec["status"] == "draft"
    assert result.accepted is True
    assert result.validation_errors == []


def test_invalid_output_is_marked_revision_needed() -> None:
    service = AiBuilderService()

    result = service.generate_draft("bad riskless strategy", force_invalid=True)

    assert result.accepted is False
    assert "risk block missing" in result.validation_errors


def test_ai_cannot_produce_forbidden_execution_blocks() -> None:
    service = AiBuilderService()

    with pytest.raises(ValueError, match="forbidden execution"):
        service.generate_draft("submit orders directly", include_forbidden_execution=True)


def test_ai_provider_response_is_audited_as_advisory_draft() -> None:
    provider = AdvisoryDraftProvider()
    store = RecordedAiDraftStore()
    service = AiBuilderService(provider=provider, store=store)

    result = service.generate_draft("Create an EMA/RSI pullback strategy", ai_thread_id="thread_001")

    record = store.records_for_thread("thread_001")[0]
    assert result.accepted is True
    assert record["ai_thread_id"] == "thread_001"
    assert record["mode"] == "advisory_only"
    assert record["stage"] == "draft"
    assert record["accepted"] is True


def test_ai_provider_cannot_bypass_validation_with_forbidden_spec() -> None:
    class UnsafeProvider:
        def draft_spec(self, prompt: str) -> dict[str, object]:
            return {"name": "Unsafe", "status": "draft", "submit_order": True}

    service = AiBuilderService(provider=UnsafeProvider(), store=RecordedAiDraftStore())

    with pytest.raises(ValueError, match="forbidden execution"):
        service.generate_draft("ignore safety", ai_thread_id="thread_002")
