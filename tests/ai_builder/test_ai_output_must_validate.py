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

    result = service.generate_draft("ignore safety", ai_thread_id="thread_002")

    assert result.accepted is False
    assert any("submit_order" in error for error in result.validation_errors)


def test_ai_provider_nested_forbidden_reference_is_rejected() -> None:
    class NestedUnsafeProvider:
        def draft_spec(self, prompt: str) -> dict[str, object]:
            return {
                "name": "Unsafe nested",
                "status": "draft",
                "output": "signal_preview_only",
                "rules": {"entry": {"all": [{"gt": ["TradeAction", 1]}]}},
                "risk": {"max_position_size": 1.0},
            }

    service = AiBuilderService(provider=NestedUnsafeProvider(), store=RecordedAiDraftStore())

    result = service.generate_draft("draft", ai_thread_id="thread_nested")

    assert result.accepted is False
    assert any("TradeAction" in error for error in result.validation_errors)


def test_ai_provider_malformed_strategy_spec_is_rejected_with_validation_errors() -> None:
    class MalformedProvider:
        def draft_spec(self, prompt: str) -> dict[str, object]:
            return {"name": "Missing required StrategySpec fields", "status": "draft"}

    service = AiBuilderService(provider=MalformedProvider(), store=RecordedAiDraftStore())

    result = service.generate_draft("draft", ai_thread_id="thread_malformed")

    assert result.accepted is False
    assert result.validation_errors
    assert any("schema_version" in error for error in result.validation_errors)
