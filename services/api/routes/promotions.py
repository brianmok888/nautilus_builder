from __future__ import annotations

from packages.promotions.service import PromotionService
from services.api.router import ApiResponse


def create_shadow_payload(strategy_version: str, compile_hash: str) -> dict[str, object]:
    service = PromotionService()
    request = service.create_shadow_request(
        strategy_version=strategy_version,
        compile_hash=compile_hash,
        gate_compatibility=True,
    )
    return request.model_dump(mode="json")


def request_promotion_payload(payload: dict[str, object]) -> ApiResponse:
    target = str(payload.get("target", ""))
    if target not in {"shadow", "signal-preview"}:
        return ApiResponse({"error": "unsupported_promotion_target", "target": target}, status_code=422)
    return ApiResponse(
        {
            "strategy_version_id": str(payload["strategy_version_id"]),
            "result_id": str(payload["result_id"]),
            "target": target,
            "manual_approval_required": True,
            "mode": "builder_safe_promotion_request",
        },
        status_code=201,
    )
