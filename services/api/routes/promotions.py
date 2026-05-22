from __future__ import annotations

from packages.promotions.service import PromotionService


def create_shadow_payload(strategy_version: str, compile_hash: str) -> dict[str, object]:
    service = PromotionService()
    request = service.create_shadow_request(
        strategy_version=strategy_version,
        compile_hash=compile_hash,
        gate_compatibility=True,
    )
    return request.model_dump(mode="json")
