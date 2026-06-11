"""Promotion gate — evaluates evidence sets for promotion decisions.

Hard rules:
- Builder may produce shadow_signal_preview / paper_ready style readiness only
- Builder must not mark anything as live-ready by itself
"""
from __future__ import annotations


from enum import Enum

from pydantic import BaseModel, Field


class PromotionLevel(str, Enum):
    DRAFT = "draft"
    VALIDATED = "validated"
    COMPILED = "compiled"
    BACKTESTED_SYNTHETIC = "backtested_synthetic"
    BACKTESTED_CATALOG = "backtested_catalog"
    SHADOW_SIGNAL_PREVIEW = "shadow_signal_preview"
    PAPER_READY = "paper_ready"
    LIVE_CANDIDATE_EXTERNAL_ONLY = "live_candidate_external_only"


class PromotionEvidenceSet(BaseModel):
    compile_artifact_ref: str = ""
    validation_result_ref: str = ""
    replay_manifest_ref: str = ""
    backtest_result_ref: str = ""
    dataset_manifest_refs: list[str] = Field(default_factory=list)
    manual_review_ref: str = ""
    data_tester_ref: str = ""
    exec_tester_ref: str = ""
    reconciliation_ref: str = ""
    is_synthetic_backtest: bool = False




class PromotionResult(BaseModel):
    allowed: bool
    promotion_level: PromotionLevel
    blocking_reason_code: str = ""
    blocking_evidence_id: str = ""
    human_readable_message: str = ""
    machine_readable_reason_code: str = ""


class PromotionGate:
    """Evaluates whether a promotion evidence set supports the requested level."""

    def evaluate(
        self,
        evidence: PromotionEvidenceSet,
        target_level: PromotionLevel,
    ) -> PromotionResult:
        # Live candidate is always out of scope for Builder
        if target_level == PromotionLevel.LIVE_CANDIDATE_EXTERNAL_ONLY:
            return PromotionResult(
                allowed=False,
                promotion_level=target_level,
                blocking_reason_code="LIVE_READINESS_OUT_OF_SCOPE",
                human_readable_message="Live candidate readiness requires external Daedalus/DataTester/ExecTester evidence",
                machine_readable_reason_code="LIVE_READINESS_OUT_OF_SCOPE",
            )

        # Compiled level requires compile artifact
        if target_level.value in ("compiled", "backtested_synthetic", "backtested_catalog", "shadow_signal_preview", "paper_ready"):
            if not evidence.compile_artifact_ref:
                return PromotionResult(
                    allowed=False,
                    promotion_level=target_level,
                    blocking_reason_code="COMPILE_ARTIFACT_MISSING",
                    human_readable_message="Compile artifact reference is required",
                    machine_readable_reason_code="COMPILE_ARTIFACT_MISSING",
                )

        # Catalog backtest requires non-synthetic backtest evidence
        if target_level == PromotionLevel.BACKTESTED_CATALOG:
            if not evidence.backtest_result_ref:
                return PromotionResult(
                    allowed=False,
                    promotion_level=target_level,
                    blocking_reason_code="BACKTEST_RESULT_MISSING",
                    human_readable_message="Backtest result reference is required for catalog level",
                    machine_readable_reason_code="BACKTEST_RESULT_MISSING",
                )
            if evidence.is_synthetic_backtest:
                return PromotionResult(
                    allowed=False,
                    promotion_level=target_level,
                    blocking_reason_code="SYNTHETIC_BACKTEST_CANNOT_SATISFY_CATALOG",
                    human_readable_message="Synthetic backtest cannot satisfy catalog backtest requirement",
                    machine_readable_reason_code="SYNTHETIC_BACKTEST_CANNOT_SATISFY_CATALOG",
                )

        # Shadow signal preview allowed with compile + validation + backtest
        if target_level == PromotionLevel.SHADOW_SIGNAL_PREVIEW:
            if not evidence.validation_result_ref:
                return PromotionResult(
                    allowed=False,
                    promotion_level=target_level,
                    blocking_reason_code="VALIDATION_RESULT_MISSING",
                    human_readable_message="Validation result reference is required",
                    machine_readable_reason_code="VALIDATION_RESULT_MISSING",
                )
            if not evidence.backtest_result_ref:
                return PromotionResult(
                    allowed=False,
                    promotion_level=target_level,
                    blocking_reason_code="BACKTEST_RESULT_MISSING",
                    human_readable_message="Backtest result reference is required",
                    machine_readable_reason_code="BACKTEST_RESULT_MISSING",
                )
            return PromotionResult(
                allowed=True,
                promotion_level=target_level,
                human_readable_message="Shadow signal preview allowed with verified evidence",
            )

        # Default: allowed for lower levels
        return PromotionResult(
            allowed=True,
            promotion_level=target_level,
            human_readable_message=f"Promotion to {target_level.value} allowed",
        )
