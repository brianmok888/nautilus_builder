"""Tests for promotion evidence policy."""
from __future__ import annotations

from packages.promotions.evidence_policy import (
    BLOCKING_REASONS,
    REQUIRED_EVIDENCE,
    get_required_evidence,
)
from packages.promotions.gate import PromotionGate, PromotionEvidenceSet, PromotionLevel


class TestEvidencePolicy:
    def test_validated_requires_validation_and_compile(self):
        required = get_required_evidence(PromotionLevel.VALIDATED)
        assert "validation_report" in required
        assert "compile_artifact" in required

    def test_catalog_backtest_requires_real_data(self):
        required = get_required_evidence(PromotionLevel.BACKTESTED_CATALOG)
        assert "catalog_dataset_manifest" in required
        assert "real_dataset_backtest_result" in required

    def test_live_candidate_requires_all(self):
        required = get_required_evidence(PromotionLevel.LIVE_CANDIDATE_EXTERNAL_ONLY)
        assert "exec_tester_report" in required
        assert "reconciliation_report" in required
        assert "manual_review" in required

    def test_blocking_reasons_cover_spec(self):
        expected = {
            "BLOCK_VALIDATION_FAILED",
            "BLOCK_COMPILE_ARTIFACT_MISSING",
            "BLOCK_EVIDENCE_MISSING",
            "BLOCK_SYNTHETIC_ONLY_REPLAY",
            "BLOCK_AUTHORITY_BOUNDARY_VIOLATION",
        }
        assert expected.issubset(BLOCKING_REASONS)


class TestPromotionGate:
    def test_live_candidate_blocked(self):
        gate = PromotionGate()
        evidence = PromotionEvidenceSet(
            compile_artifact_ref="ref_001",
            validation_result_ref="ref_002",
        )
        result = gate.evaluate(evidence, PromotionLevel.LIVE_CANDIDATE_EXTERNAL_ONLY)
        assert not result.allowed
        assert "OUT_OF_SCOPE" in result.blocking_reason_code

    def test_synthetic_cannot_satisfy_catalog(self):
        gate = PromotionGate()
        evidence = PromotionEvidenceSet(
            compile_artifact_ref="ref_001",
            backtest_result_ref="ref_bt",
            is_synthetic_backtest=True,
        )
        result = gate.evaluate(evidence, PromotionLevel.BACKTESTED_CATALOG)
        assert not result.allowed
        assert "SYNTHETIC" in result.blocking_reason_code

    def test_shadow_signal_allowed_with_evidence(self):
        gate = PromotionGate()
        evidence = PromotionEvidenceSet(
            compile_artifact_ref="ref_001",
            validation_result_ref="ref_vr",
            backtest_result_ref="ref_bt",
        )
        result = gate.evaluate(evidence, PromotionLevel.SHADOW_SIGNAL_PREVIEW)
        assert result.allowed
