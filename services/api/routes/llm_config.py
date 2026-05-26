from __future__ import annotations

from packages.llm_config import LlmConfigService
from services.api.router import ApiResponse


def get_llm_config_payload(service: LlmConfigService) -> dict[str, object]:
    return service.get_config()


def save_llm_config_payload(service: LlmConfigService, payload: dict[str, object]) -> ApiResponse:
    try:
        return ApiResponse(service.save_config(payload))
    except ValueError as exc:
        return ApiResponse({"error": "invalid_llm_config", "details": str(exc)}, status_code=422)
