from __future__ import annotations

from pydantic import ValidationError

from packages.llm_config.models import LlmConfig

_FORBIDDEN_SECRET_KEYS = {
    "api_key",
    "openai_api_key",
    "secret",
    "secret_key",
    "authorization",
    "auth_token",
    "bearer_token",
    "password",
}


class LlmConfigService:
    def __init__(self, initial: LlmConfig | None = None) -> None:
        self._config = initial or LlmConfig()

    def get_config(self) -> dict[str, object]:
        return _response_payload(self._config)

    def save_config(self, payload: dict[str, object]) -> dict[str, object]:
        secret_key = _find_forbidden_secret_key(payload)
        if secret_key is not None:
            raise ValueError(f"browser LLM config must not include secret field: {secret_key}")
        try:
            config = LlmConfig.model_validate(payload)
        except ValidationError as exc:
            raise ValueError(str(exc)) from exc
        self._config = config
        return _response_payload(config)


def _response_payload(config: LlmConfig) -> dict[str, object]:
    return {
        "provider_type": config.provider_type.value,
        "base_url": config.base_url,
        "roles": {
            "draft_strategy_spec": config.draft_model,
            "validate_and_repair": config.validation_model,
            "explain_operator_feedback": config.explanation_model,
        },
        "guardrails": {
            "output_mode": "signal_preview_only",
            "validation_gate": "validate_strategy_spec()",
            "promotion": "manual only",
            "live_order_authority": False,
        },
        "credential_inputs_allowed": config.credential_inputs_allowed,
        "secrets_storage": config.secrets_storage,
    }


def _find_forbidden_secret_key(value: object) -> str | None:
    if isinstance(value, dict):
        for key, nested_value in value.items():
            normalized = str(key).strip().lower()
            if normalized in _FORBIDDEN_SECRET_KEYS:
                return str(key)
            nested = _find_forbidden_secret_key(nested_value)
            if nested is not None:
                return nested
    elif isinstance(value, list):
        for item in value:
            nested = _find_forbidden_secret_key(item)
            if nested is not None:
                return nested
    return None
