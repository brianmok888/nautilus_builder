"""Tests for prompt redaction before audit storage (M-06 closure)."""
from __future__ import annotations

from packages.ai_builder.service import _redact_prompt


class TestPromptRedaction:
    def test_redaction_returns_prompt_hash(self) -> None:
        redacted, prompt_hash = _redact_prompt("Create an EMA crossover strategy")
        assert len(prompt_hash) == 64
        assert prompt_hash != "Create an EMA crossover strategy"

    def test_redaction_is_deterministic(self) -> None:
        _, hash1 = _redact_prompt("Same prompt")
        _, hash2 = _redact_prompt("Same prompt")
        assert hash1 == hash2

    def test_redaction_strips_api_key_values(self) -> None:
        redacted, _ = _redact_prompt("Use api_key=sk-abc123456789 for the provider")
        assert "sk-abc123456789" not in redacted
        assert "[REDACTED]" in redacted

    def test_redaction_strips_bearer_tokens(self) -> None:
        redacted, _ = _redact_prompt("Set Bearer eyJhbGciOiJIUzI1NiJ9 as auth")
        assert "eyJhbGciOiJIUzI1NiJ9" not in redacted
        assert "[REDACTED]" in redacted

    def test_redaction_preserves_non_secret_content(self) -> None:
        redacted, _ = _redact_prompt("Create an RSI strategy with period 14")
        assert redacted == "Create an RSI strategy with period 14"

    def test_audit_record_contains_redacted_prompt_and_hash(self) -> None:
        from packages.ai_builder.provider import RecordedAiDraftStore
        store = RecordedAiDraftStore()
        service = __import__("packages.ai_builder.service", fromlist=["AiBuilderService"]).AiBuilderService(store=store)
        service.generate_draft("Write a momentum strategy")
        records = store.records_for_thread("anonymous_thread")
        assert len(records) == 1
        assert "prompt_hash" in records[0]
        assert len(records[0]["prompt_hash"]) == 64
        # Original prompt text is still the redacted version
        assert records[0]["prompt"] == "Write a momentum strategy"
