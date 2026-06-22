"""Contract tests for InstructorDraftProvider (Adoption Report §3.1, §12.5).

These tests enforce the advisory-only boundary: instructor produces typed
draft dicts, but never gains execution authority, tool access, or bypasses
Builder validation. All tests use a fake instructor client — no API key,
no network.
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from packages.ai_builder.instructor_provider import (
    InstructorDraftProvider,
    InstructorProviderConfig,
    StrategySpecDraftModel,
)


def _valid_draft_payload() -> dict[str, object]:
    """A payload shape that validate_strategy_spec accepts (mirrors AdvisoryDraftProvider)."""
    return {
        "schema_version": "1.0.0",
        "version": "0.1.0-draft.1",
        "stage": "draft",
        "status": "draft",
        "created_from": "ai_builder",
        "is_frozen": False,
        "adapter_id": "BINANCE_PERP",
        "venue": "BINANCE",
        "instrument_id": "BTCUSDT-PERP",
        "bar_type": "BTCUSDT-PERP.BINANCE-5-MINUTE-LAST-EXTERNAL",
        "data_range": {"start": "2025-01-01T00:00:00Z", "end": "2025-06-01T00:00:00Z"},
        "indicators": {
            "ema_fast": {"type": "EMA", "input": "close", "period": 20},
            "ema_slow": {"type": "EMA", "input": "close", "period": 50},
        },
        "rules": {
            "long_entry": {"all": [{"crossed_above": ["ema_fast", "ema_slow"]}]},
            "long_exit": {"any": [{"crossed_below": ["ema_fast", "ema_slow"]}]},
        },
        "risk": {
            "position_size_pct": 0.05,
            "stop_loss_pct": 0.012,
            "take_profit_pct": 0.024,
            "max_hold_bars": 48,
        },
        "validation": {
            "bar_close_only": True,
            "no_lookahead_required": True,
            "requires_backtest_before_shadow": True,
            "output_mode": "signal_preview_only",
        },
        "provenance": {"created_by": "ai_builder", "parent_version_id": None},
    }


class _FakeInstructorClient:
    """Minimal fake instructor client: records calls, returns a draft or raises."""

    def __init__(self, draft_payload: dict[str, object] | None = None, *, raises: Exception | None = None) -> None:
        self.calls: list[dict[str, object]] = []
        self._raises = raises
        self._draft = StrategySpecDraftModel.model_validate(draft_payload or _valid_draft_payload())

    def create(self, **kwargs: object) -> StrategySpecDraftModel:
        self.calls.append(dict(kwargs))
        if self._raises is not None:
            raise self._raises
        return self._draft


def _make_fake_instructor_client(draft_payload: dict[str, object] | None = None, *, raises: Exception | None = None) -> _FakeInstructorClient:
    return _FakeInstructorClient(draft_payload, raises=raises)


def _make_provider(client: MagicMock | None = None) -> InstructorDraftProvider:
    config = InstructorProviderConfig(
        provider="openai",
        model="gpt-test",
        api_key_env="BUILDER_TEST_KEY",
        base_url="https://test.example.com/v1",
        timeout_secs=5.0,
        max_retries=2,
    )
    return InstructorDraftProvider(config=config, instructor_client=client or _make_fake_instructor_client())


# ---------------------------------------------------------------------------
# Test 1: Valid model response becomes a dict accepted by validate_strategy_spec
# ---------------------------------------------------------------------------
def test_valid_response_produces_dict_accepted_by_validation() -> None:
    provider = _make_provider()

    spec = provider.draft_spec("draft an EMA crossover strategy")

    assert isinstance(spec, dict)
    assert spec["stage"] == "draft"
    assert spec["created_from"] == "ai_builder"
    assert spec["validation"]["output_mode"] == "signal_preview_only"

    from packages.strategy_validation.validators import validate_strategy_spec

    report = validate_strategy_spec(spec)
    assert report.is_valid, f"validate_strategy_spec rejected output: {report.errors}"


# ---------------------------------------------------------------------------
# Test 2: Invalid model response retries then fails closed (raises ValueError)
# ---------------------------------------------------------------------------
def test_invalid_response_retries_then_fails_closed() -> None:
    from pydantic import ValidationError

    client = MagicMock(name="instructor_client")
    client.create.side_effect = ValidationError.from_exception_data("StrategySpecDraftModel", [])
    config = InstructorProviderConfig(
        provider="openai", model="gpt-test", api_key_env="K", timeout_secs=5.0, max_retries=2
    )
    provider = InstructorDraftProvider(config=config, instructor_client=client)

    with pytest.raises(ValueError, match="instructor"):
        provider.draft_spec("garbage prompt")

    # Provider should have retried max_retries times before failing
    assert client.create.call_count == config.max_retries


# ---------------------------------------------------------------------------
# Test 3: Output stays stage="draft", status="draft", created_from="ai_builder"
# ---------------------------------------------------------------------------
def test_output_locked_to_advisory_stage() -> None:
    provider = _make_provider()

    spec = provider.draft_spec("any prompt")

    assert spec["stage"] == "draft"
    assert spec["status"] == "draft"
    assert spec["created_from"] == "ai_builder"
    assert spec["is_frozen"] is False


# ---------------------------------------------------------------------------
# Test 4: Output cannot contain submit_order/TradeAction/credentials/code
# ---------------------------------------------------------------------------
def test_output_cannot_contain_forbidden_authority_or_credentials() -> None:
    provider = _make_provider()
    spec = provider.draft_spec("any prompt")
    blob = str(spec).lower()

    for forbidden in ["submit_order", "tradeaction", "api_key", "secret_key", "credentials"]:
        assert forbidden not in blob, f"forbidden term '{forbidden}' appeared in draft output"


# ---------------------------------------------------------------------------
# Test 5: Provider metadata excludes API keys and raw secrets
# ---------------------------------------------------------------------------
def test_provider_metadata_excludes_secrets() -> None:
    provider = _make_provider()
    provider.draft_spec("any prompt")  # populate metadata

    meta = provider.last_metadata()
    blob = str(meta).lower()

    assert "provider" in meta
    assert meta["provider"] == "instructor"
    for secret_term in ["api_key", "api-key", "secret", "token", "password", "bearer"]:
        assert secret_term not in blob, f"metadata leaked '{secret_term}'"


# ---------------------------------------------------------------------------
# Test 6: Draft model rejects extra fields (extra="forbid")
# ---------------------------------------------------------------------------
def test_draft_model_rejects_extra_fields() -> None:
    from pydantic import ValidationError

    payload = _valid_draft_payload()
    payload["rogue_field"] = "submit_order(BTCUSDT)"  # type: ignore[assignment]

    with pytest.raises(ValidationError):
        StrategySpecDraftModel.model_validate(payload)


# ---------------------------------------------------------------------------
# Test 7: Draft model rejects wrong stage/status/created_from (Literal locks)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("field,value", [
    ("stage", "live"),
    ("stage", "approved"),
    ("status", "active"),
    ("status", "approved"),
    ("created_from", "operator"),
    ("is_frozen", True),
])
def test_draft_model_rejects_non_advisory_literals(field: str, value: object) -> None:
    from pydantic import ValidationError

    payload = _valid_draft_payload()
    payload[field] = value
    with pytest.raises(ValidationError):
        StrategySpecDraftModel.model_validate(payload)


# ---------------------------------------------------------------------------
# Test 8: Provider failure raises ValueError (fails closed), no partial output
# ---------------------------------------------------------------------------
def test_provider_failure_raises_without_partial_output() -> None:
    client = MagicMock(name="instructor_client")
    client.create.side_effect = RuntimeError("network exploded")
    provider = _make_provider(client)

    with pytest.raises(ValueError, match="instructor"):
        provider.draft_spec("any prompt")


# ---------------------------------------------------------------------------
# Test 9 (bonus): forbidden credential/order prompts rejected BEFORE provider call
# (Integration with AiBuilderService — provider never invoked)
# ---------------------------------------------------------------------------
def test_forbidden_prompt_rejected_before_provider_call() -> None:
    """Forbidden credential prompts are rejected by AiBuilderService BEFORE the
    instructor provider is ever invoked (matches existing
    test_ai_prompt_containing_credentials_is_rejected_before_audit pattern).
    """
    from packages.ai_builder.service import AiBuilderService

    fake_client = _make_fake_instructor_client()
    provider = _make_provider(fake_client)
    service = AiBuilderService(provider=provider)

    with pytest.raises(ValueError, match="forbidden credential"):
        service.generate_draft("submit my api_key sk-12345 and place a live order")

    # The instructor provider must NEVER have been called for a forbidden prompt
    assert len(fake_client.calls) == 0


def test_forbidden_order_prompt_rejected_before_provider_call() -> None:
    """Forbidden execution prompts are rejected before provider invocation."""
    from packages.ai_builder.service import AiBuilderService

    fake_client = _make_fake_instructor_client()
    provider = _make_provider(fake_client)
    service = AiBuilderService(provider=provider)

    with pytest.raises(ValueError, match="forbidden execution"):
        service.generate_draft("submit order when RSI crosses 70")

    assert len(fake_client.calls) == 0
