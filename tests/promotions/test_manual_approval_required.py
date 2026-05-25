from __future__ import annotations

import pytest

from packages.promotions.service import PromotionService


def test_final_promotion_requires_manual_approval() -> None:
    service = PromotionService()

    with pytest.raises(ValueError, match="manual approval"):
        service.create_final_candidate(
            strategy_version="0.3.0-beta.1",
            compile_hash="abc123",
            gate_compatibility=True,
            manual_approval=False,
            evidence_refs={
                "validation_report": "artifact://validation/vr_001.json",
                "backtest_result": "artifact://backtests/bt_001/result.json",
                "no_lookahead_report": "artifact://validation/no_lookahead_001.json",
                "gate_compatibility_report": "artifact://gate/gate_compat_001.json",
                "runtime_boundary_report": "artifact://runtime/boundary_001.json",
                "risk_review": "artifact://risk/risk_review_001.json",
            },
        )
