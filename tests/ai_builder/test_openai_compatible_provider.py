from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from packages.ai_builder.provider import (
    AdvisoryDraftProvider,
    OpenAICompatibleDraftProvider,
    OpenAICompatibleProviderConfig,
    build_default_draft_provider,
)
from packages.ai_builder.service import AiBuilderService
from packages.ai_builder.provider import RecordedAiDraftStore


def _valid_strategy_spec() -> dict[str, object]:
    return AdvisoryDraftProvider().draft_spec("EMA RSI")


class CapturingTransport:
    def __init__(self, response: dict[str, object]) -> None:
        self.response = response
        self.calls: list[tuple[str, dict[str, str], dict[str, object], float]] = []

    def __call__(
        self,
        url: str,
        headers: dict[str, str],
        payload: dict[str, object],
        timeout_secs: float,
    ) -> dict[str, object]:
        self.calls.append((url, headers, payload, timeout_secs))
        return self.response


def _chat_response(content: object, *, response_id: str = "chatcmpl_test") -> dict[str, object]:
    return {
        "id": response_id,
        "model": "provider-response-model",
        "choices": [
            {
                "finish_reason": "stop",
                "message": {"content": content},
            }
        ],
        "usage": {"prompt_tokens": 11, "completion_tokens": 17, "total_tokens": 28},
    }


def test_provider_config_from_env_requires_complete_openai_compatible_settings() -> None:
    assert OpenAICompatibleProviderConfig.from_env({}) is None
    assert OpenAICompatibleProviderConfig.from_env({"OPENAI_API_KEY": "sk-test"}) is None

    config = OpenAICompatibleProviderConfig.from_env(
        {
            "OPENAI_API_KEY": "sk-test",
            "OPENAI_BASE_URL": "https://api.example.test/v1",
            "OPENAI_MODEL": "builder-json-model",
        }
    )

    assert config is not None
    assert config.api_key == "sk-test"
    assert config.base_url == "https://api.example.test/v1"
    assert config.model == "builder-json-model"
    assert "sk-test" not in repr(config)


def test_default_provider_uses_openai_compatible_provider_only_when_env_is_complete() -> None:
    assert isinstance(build_default_draft_provider({}), AdvisoryDraftProvider)

    provider = build_default_draft_provider(
        {
            "OPENAI_API_KEY": "sk-test",
            "OPENAI_BASE_URL": "https://api.example.test",
            "OPENAI_MODEL": "builder-json-model",
        }
    )

    assert isinstance(provider, OpenAICompatibleDraftProvider)


def test_openai_provider_posts_chat_completions_payload_and_returns_strategy_spec() -> None:
    spec = _valid_strategy_spec()
    transport = CapturingTransport(_chat_response(json.dumps(spec), response_id="chatcmpl_strategy"))
    provider = OpenAICompatibleDraftProvider(
        OpenAICompatibleProviderConfig(
            api_key="sk-secret-value",
            base_url="https://api.example.test",
            model="builder-json-model",
            timeout_secs=12.5,
        ),
        transport=transport,
    )

    drafted = provider.draft_spec("Build an EMA RSI pullback strategy for BTC")

    assert drafted == spec
    assert len(transport.calls) == 1
    url, headers, payload, timeout_secs = transport.calls[0]
    assert url == "https://api.example.test/v1/chat/completions"
    assert headers["Authorization"] == "Bearer sk-secret-value"
    assert headers["Content-Type"] == "application/json"
    assert payload["model"] == "builder-json-model"
    assert payload["response_format"] == {"type": "json_object"}
    assert timeout_secs == 12.5

    messages = payload["messages"]
    assert isinstance(messages, list)
    assert any(isinstance(message, Mapping) and message.get("role") == "user" and "EMA RSI" in str(message.get("content", "")) for message in messages)
    assert any(isinstance(message, Mapping) and "signal_preview_only" in str(message.get("content", "")) for message in messages)
    assert any(isinstance(message, Mapping) and "submit_order" in str(message.get("content", "")) for message in messages)


def test_ai_builder_service_audits_prompt_and_openai_response_metadata_without_api_key() -> None:
    spec = _valid_strategy_spec()
    transport = CapturingTransport(_chat_response(json.dumps(spec), response_id="chatcmpl_audit"))
    provider = OpenAICompatibleDraftProvider(
        OpenAICompatibleProviderConfig(
            api_key="sk-secret-value",
            base_url="https://api.example.test/v1",
            model="builder-json-model",
        ),
        transport=transport,
    )
    store = RecordedAiDraftStore()
    service = AiBuilderService(provider=provider, store=store)

    result = service.generate_draft("Create an EMA RSI StrategySpec", ai_thread_id="thread_openai")

    assert result.accepted is True
    record = store.records_for_thread("thread_openai")[0]
    assert record["prompt"] == "Create an EMA RSI StrategySpec"
    assert record["provider"] == "openai_compatible"
    assert record["validation_errors"] == []
    metadata = record["provider_metadata"]
    assert isinstance(metadata, dict)
    assert metadata["provider"] == "openai_compatible"
    assert metadata["model"] == "builder-json-model"
    assert metadata["endpoint_url"] == "https://api.example.test/v1/chat/completions"
    assert metadata["response_id"] == "chatcmpl_audit"
    assert metadata["finish_reason"] == "stop"
    assert metadata["usage"] == {"prompt_tokens": 11, "completion_tokens": 17, "total_tokens": 28}
    assert "sk-secret-value" not in json.dumps(record, sort_keys=True)


def test_openai_provider_malformed_json_is_rejected_and_audited() -> None:
    transport = CapturingTransport(_chat_response("not json", response_id="chatcmpl_bad_json"))
    provider = OpenAICompatibleDraftProvider(
        OpenAICompatibleProviderConfig(
            api_key="sk-secret-value",
            base_url="https://api.example.test/v1",
            model="builder-json-model",
        ),
        transport=transport,
    )
    store = RecordedAiDraftStore()
    service = AiBuilderService(provider=provider, store=store)

    result = service.generate_draft("Create malformed", ai_thread_id="thread_bad_json")

    assert result.accepted is False
    assert result.spec == {}
    assert any("strict StrategySpec JSON" in error for error in result.validation_errors)
    record = store.records_for_thread("thread_bad_json")[0]
    assert record["accepted"] is False
    assert record["provider_metadata"]["response_id"] == "chatcmpl_bad_json"
    assert "sk-secret-value" not in json.dumps(record, sort_keys=True)


def test_openai_provider_forbidden_model_output_still_fails_strategy_validation() -> None:
    unsafe_spec: dict[str, Any] = _valid_strategy_spec()
    unsafe_spec["rules"] = {
        "long_entry": {"all": [{"gt": ["api_key", 1]}]},
        "long_exit": {"any": [{"lt": ["rsi", 45]}]},
    }
    transport = CapturingTransport(_chat_response(json.dumps(unsafe_spec), response_id="chatcmpl_forbidden"))
    provider = OpenAICompatibleDraftProvider(
        OpenAICompatibleProviderConfig(
            api_key="sk-secret-value",
            base_url="https://api.example.test/v1",
            model="builder-json-model",
        ),
        transport=transport,
    )
    service = AiBuilderService(provider=provider, store=RecordedAiDraftStore())

    result = service.generate_draft("Create strategy but leak key", ai_thread_id="thread_forbidden")

    assert result.accepted is False
    assert any("api_key" in error for error in result.validation_errors)


def test_ai_prompt_containing_credentials_is_rejected_before_audit() -> None:
    store = RecordedAiDraftStore()
    service = AiBuilderService(store=store)

    try:
        service.generate_draft("Use API key sk-should-not-be-stored", ai_thread_id="thread_secret_prompt")
    except ValueError as exc:
        assert "forbidden credential" in str(exc)
    else:  # pragma: no cover - assertion path should not be reached
        raise AssertionError("credential prompt was accepted")

    assert store.records_for_thread("thread_secret_prompt") == []


def test_fastapi_production_mode_requires_durable_ai_audit_store(monkeypatch) -> None:
    import sys
    import types

    class FakeFastAPI:
        def __init__(self, *, title: str, version: str) -> None:
            self.title = title
            self.version = version
        def get(self, _path):
            return lambda handler: handler
        def post(self, _path):
            return lambda handler: handler

    monkeypatch.setitem(sys.modules, "fastapi", types.SimpleNamespace(FastAPI=FakeFastAPI, Header=lambda default=None: default))
    monkeypatch.setitem(sys.modules, "fastapi.responses", types.SimpleNamespace(JSONResponse=object))
    monkeypatch.setenv("BUILDER_ENV", "production")
    monkeypatch.setenv("BUILDER_API_TOKEN", "prod-token-1234567890-1234567890")
    monkeypatch.setenv("BUILDER_CORS_ORIGINS", "https://builder.example.com")
    monkeypatch.delenv("BUILDER_AI_AUDIT_SQLITE_PATH", raising=False)

    from services.api.fastapi_app import create_fastapi_app

    try:
        create_fastapi_app()
    except ValueError as exc:
        assert "durable AI audit store is required" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("production FastAPI app started without durable AI audit store")
