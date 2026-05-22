from __future__ import annotations

from .models import LifecycleStage, PromotionEvidence


def require_promotion_evidence(*, from_stage: LifecycleStage, to_stage: LifecycleStage, evidence: PromotionEvidence) -> None:
    if from_stage == LifecycleStage.DRAFT and to_stage == LifecycleStage.TESTING:
        if not evidence.validation_passed:
            raise ValueError("validation evidence is required")
        return

    if from_stage == LifecycleStage.TESTING and to_stage == LifecycleStage.BETA:
        if not evidence.backtest_succeeded:
            raise ValueError("backtest evidence is required")
        if not evidence.no_lookahead_passed:
            raise ValueError("no-lookahead evidence is required")
        return

    if from_stage == LifecycleStage.BETA and to_stage == LifecycleStage.FINAL:
        if not evidence.shadow_evidence:
            raise ValueError("shadow evidence is required")
        if not evidence.gate_compatibility:
            raise ValueError("gate compatibility is required")
        if not evidence.manual_approval:
            raise ValueError("manual approval is required")
        return

    raise ValueError(f"unsupported promotion path: {from_stage.value} -> {to_stage.value}")
