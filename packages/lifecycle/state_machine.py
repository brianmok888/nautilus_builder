from __future__ import annotations

from .models import LifecycleStage, PromotionEvidence
from .promotion_policy import require_promotion_evidence


def promote_stage(*, from_stage: LifecycleStage, to_stage: LifecycleStage, evidence: PromotionEvidence) -> LifecycleStage:
    require_promotion_evidence(from_stage=from_stage, to_stage=to_stage, evidence=evidence)
    return to_stage
