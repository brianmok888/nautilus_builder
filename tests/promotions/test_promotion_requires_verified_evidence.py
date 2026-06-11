"""Promotion gate hardening tests — Segment 8."""
import pytest

from packages.evidence_ledger.models import ArtifactType, EvidenceRef, VerificationStatus
from packages.promotions.gate import (
    PromotionEvidenceSet,
    PromotionGate,
    PromotionLevel,
)


class TestPromotionEvidenceSet:
    def test_evidence_set_fields(self) -> None:
        es = PromotionEvidenceSet(
            compile_artifact_ref="ev_compile",
            validation_result_ref="ev_validate",
            backtest_result_ref="ev_backtest",
        )
        assert es.compile_artifact_ref == "ev_compile"


class TestPromotionGate:
    def test_missing_compile_artifact_blocks(self) -> None:
        gate = PromotionGate()
        evidence = PromotionEvidenceSet(
            compile_artifact_ref="",
            validation_result_ref="ev_val",
            backtest_result_ref="ev_bt",
        )
        result = gate.evaluate(evidence, PromotionLevel.COMPILED)
        assert not result.allowed
        assert "COMPILE_ARTIFACT_MISSING" in result.blocking_reason_code

    def test_missing_backtest_blocks_catalog_level(self) -> None:
        gate = PromotionGate()
        evidence = PromotionEvidenceSet(
            compile_artifact_ref="ev_compile",
            validation_result_ref="ev_val",
            backtest_result_ref="",
        )
        result = gate.evaluate(evidence, PromotionLevel.BACKTESTED_CATALOG)
        assert not result.allowed

    def test_live_candidate_is_out_of_scope(self) -> None:
        gate = PromotionGate()
        evidence = PromotionEvidenceSet(
            compile_artifact_ref="ev_compile",
            validation_result_ref="ev_val",
            backtest_result_ref="ev_bt",
        )
        result = gate.evaluate(evidence, PromotionLevel.LIVE_CANDIDATE_EXTERNAL_ONLY)
        assert not result.allowed
        assert "OUT_OF_SCOPE" in result.blocking_reason_code or "LIVE" in result.blocking_reason_code

    def test_shadow_preview_allowed_with_evidence(self) -> None:
        gate = PromotionGate()
        evidence = PromotionEvidenceSet(
            compile_artifact_ref="ev_compile",
            validation_result_ref="ev_val",
            backtest_result_ref="ev_bt",
        )
        result = gate.evaluate(evidence, PromotionLevel.SHADOW_SIGNAL_PREVIEW)
        assert result.allowed

    def test_synthetic_cannot_satisfy_catalog(self) -> None:
        gate = PromotionGate()
        evidence = PromotionEvidenceSet(
            compile_artifact_ref="ev_compile",
            validation_result_ref="ev_val",
            backtest_result_ref="ev_bt_synthetic",
            is_synthetic_backtest=True,
        )
        result = gate.evaluate(evidence, PromotionLevel.BACKTESTED_CATALOG)
        assert not result.allowed
        assert "SYNTHETIC" in result.blocking_reason_code


class TestPromotionLevel:
    def test_levels_defined(self) -> None:
        assert PromotionLevel.DRAFT.value == "draft"
        assert PromotionLevel.VALIDATED.value == "validated"
        assert PromotionLevel.COMPILED.value == "compiled"
        assert PromotionLevel.BACKTESTED_SYNTHETIC.value == "backtested_synthetic"
        assert PromotionLevel.BACKTESTED_CATALOG.value == "backtested_catalog"
        assert PromotionLevel.SHADOW_SIGNAL_PREVIEW.value == "shadow_signal_preview"
        assert PromotionLevel.LIVE_CANDIDATE_EXTERNAL_ONLY.value == "live_candidate_external_only"
