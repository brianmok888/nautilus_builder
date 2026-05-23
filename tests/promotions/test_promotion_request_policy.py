from __future__ import annotations

import pytest

from packages.promotions.service import PromotionService


def test_builder_promotion_request_is_shadow_only_and_manual_approval_pending() -> None:
    request = PromotionService().request_builder_promotion(
        strategy_version_id="strategy_001_v002",
        result_id="res_001",
        target="shadow",
    )

    assert request["strategy_version_id"] == "strategy_001_v002"
    assert request["result_id"] == "res_001"
    assert request["target"] == "shadow"
    assert request["approval_state"] == "manual_approval_pending"
    assert request["manual_approval_required"] is True
    assert request["may_submit_order"] is False
    assert request["may_create_trade_action"] is False
    assert request["mode"] == "builder_safe_promotion_request"


@pytest.mark.parametrize("target", ["live", "paper", "final"])
def test_builder_promotion_request_rejects_non_shadow_targets(target: str) -> None:
    with pytest.raises(ValueError, match="unsupported_promotion_target"):
        PromotionService().request_builder_promotion(
            strategy_version_id="strategy_001_v002",
            result_id="res_001",
            target=target,
        )
