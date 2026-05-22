from __future__ import annotations

import pytest

from packages.lifecycle.models import LifecycleStage, PromotionEvidence
from packages.lifecycle.promotion_policy import require_promotion_evidence
from packages.lifecycle.state_machine import promote_stage


def test_draft_to_testing_requires_validation_evidence() -> None:
    with pytest.raises(ValueError, match="validation"):
        promote_stage(
            from_stage=LifecycleStage.DRAFT,
            to_stage=LifecycleStage.TESTING,
            evidence=PromotionEvidence(),
        )


def test_testing_to_beta_requires_backtest_and_no_lookahead() -> None:
    with pytest.raises(ValueError, match="backtest"):
        require_promotion_evidence(
            from_stage=LifecycleStage.TESTING,
            to_stage=LifecycleStage.BETA,
            evidence=PromotionEvidence(validation_passed=True),
        )


def test_beta_to_final_requires_shadow_gate_and_manual_approval() -> None:
    with pytest.raises(ValueError, match="manual approval"):
        require_promotion_evidence(
            from_stage=LifecycleStage.BETA,
            to_stage=LifecycleStage.FINAL,
            evidence=PromotionEvidence(
                validation_passed=True,
                backtest_succeeded=True,
                no_lookahead_passed=True,
                shadow_evidence=True,
                gate_compatibility=True,
                manual_approval=False,
            ),
        )


def test_valid_beta_to_final_promotion_passes_without_live_authority() -> None:
    evidence = PromotionEvidence(
        validation_passed=True,
        backtest_succeeded=True,
        no_lookahead_passed=True,
        shadow_evidence=True,
        gate_compatibility=True,
        manual_approval=True,
    )

    result = promote_stage(
        from_stage=LifecycleStage.BETA,
        to_stage=LifecycleStage.FINAL,
        evidence=evidence,
    )

    assert result == LifecycleStage.FINAL
