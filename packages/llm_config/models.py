from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator


class LlmProviderType(str, Enum):
    OPENAI_COMPATIBLE = "openai-compatible"
    LOCAL_OPENAI_COMPATIBLE = "local-openai-compatible"
    ADVISORY_FIXTURE = "advisory-fixture"


class LlmConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider_type: LlmProviderType = LlmProviderType.OPENAI_COMPATIBLE
    base_url: str = "https://api.openai.com/v1"
    draft_model: str = "strategy-draft-model"
    validation_model: str = "strategy-draft-model"
    explanation_model: str = "strategy-draft-model"
    credential_inputs_allowed: Literal[False] = False
    secrets_storage: Literal["server_environment"] = "server_environment"

    @field_validator("base_url")
    @classmethod
    def validate_openai_compatible_url(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped.startswith(("https://", "http://")):
            raise ValueError("base_url must be an http(s) OpenAI-compatible endpoint")
        return stripped.rstrip("/")

    @field_validator("draft_model", "validation_model", "explanation_model")
    @classmethod
    def validate_model_name(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("model names must be non-empty")
        return stripped
