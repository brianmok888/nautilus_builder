from __future__ import annotations

from packages.promotions.service import PromotionService


REQUIRED_EVIDENCE = {
    "validation_report": "artifact://validation/vr_001.json",
    "backtest_result": "artifact://backtests/bt_001/result.json",
    "no_lookahead_report": "artifact://validation/no_lookahead_001.json",
    "gate_compatibility_report": "artifact://gate/gate_compat_001.json",
    "runtime_boundary_report": "artifact://runtime/boundary_001.json",
    "risk_review": "artifact://risk/risk_review_001.json",
}


def test_builder_promotion_request_is_signal_preview_only() -> None:
    service = PromotionService()  # noqa: F841: service construction test

    request = service.create_shadow_request(
        strategy_version="0.3.0-beta.1",
        compile_hash="abc123",
        gate_compatibility=True,
        evidence_refs=REQUIRED_EVIDENCE,
    )

    assert request.profile == "signal_preview_only"
    assert request.may_submit_order is False
    assert request.may_create_trade_action is False


def test_promotion_request_carries_builder_side_evidence_refs() -> None:
    service = PromotionService()  # noqa: F841: service construction test

    request = service.create_shadow_request(
        strategy_version="0.3.0-beta.1",
        compile_hash="abc123",
        gate_compatibility=True,
        evidence_refs=REQUIRED_EVIDENCE,
    )

    assert "validation_report" in request.evidence_refs
    assert "backtest_result" in request.evidence_refs
    assert request.compile_hash == "abc123"
