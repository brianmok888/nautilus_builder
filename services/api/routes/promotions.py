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
    try:
        request = PromotionService().request_builder_promotion(
            strategy_version_id=str(payload["strategy_version_id"]),
            result_id=str(payload["result_id"]),
            target=target,
        )
    except ValueError:
        return ApiResponse({"error": "unsupported_promotion_target", "target": target}, status_code=422)
    return ApiResponse(request, status_code=201)
