from __future__ import annotations

import pytest

from packages.ai_builder.service import AiBuilderService


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
