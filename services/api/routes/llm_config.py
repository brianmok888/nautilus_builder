from __future__ import annotations

from typing import Any

from packages.llm_config import LlmConfigService
from services.api.router import ApiResponse


def get_llm_config_payload(service: LlmConfigService) -> dict[str, object]:
    return service.get_config()


def save_llm_config_payload(
    service: LlmConfigService,
    payload: dict[str, object],
    *,
    pg_config_repo: Any | None = None,
) -> ApiResponse:
    try:
        result = service.save_config(payload)
        # Persist to Postgres if available
        if pg_config_repo is not None:
            pg_config_repo.set("llm_config", dict(payload) if isinstance(payload, dict) else {"value": payload})
        return ApiResponse(result)
    except ValueError as exc:
        return ApiResponse({"error": "invalid_llm_config", "details": str(exc)}, status_code=422)
