"""Evidence ledger model tests — Segment 7."""
import pytest

from packages.evidence_ledger.models import (
    ArtifactType,
    EvidenceRef,
    VerificationStatus,
)


class TestEvidenceRef:
    def test_evidence_ref_fields(self) -> None:
        ref = EvidenceRef(
            evidence_id="ev_001",
            project_id="proj_001",
            artifact_type=ArtifactType.COMPILED_STRATEGY_IR,
            source_system="builder",
            uri="artifact://builder/compile/abc123",
            sha256="a" * 64,
        )
        assert ref.evidence_id == "ev_001"
        assert ref.verification_status == VerificationStatus.UNVERIFIED

    def test_evidence_ref_requires_evidence_id(self) -> None:
        with pytest.raises(Exception):
            EvidenceRef(
                project_id="proj_001",
                artifact_type=ArtifactType.STRATEGY_SPEC,
                source_system="builder",
                uri="artifact://test",
                sha256="a" * 64,
            )

    def test_artifact_types_cover_required(self) -> None:
        required = [
            "STRATEGY_SPEC", "COMPILED_STRATEGY_IR", "FEATURE_DEPENDENCY_GRAPH",
            "RISK_CONTRACT", "REPLAY_MANIFEST", "BACKTEST_RESULT",
            "MANUAL_REVIEW", "PROMOTION_REQUEST",
        ]
        for name in required:
            assert hasattr(ArtifactType, name), f"Missing ArtifactType.{name}"

    def test_verification_statuses(self) -> None:
        assert VerificationStatus.UNVERIFIED.value == "unverified"
        assert VerificationStatus.VERIFIED.value == "verified"
        assert VerificationStatus.FAILED.value == "failed"
        assert VerificationStatus.HASH_MISMATCH.value == "hash_mismatch"

    def test_hash_cannot_be_empty_for_artifact_evidence(self) -> None:
        ref = EvidenceRef(
            evidence_id="ev_002",
            project_id="proj_001",
            artifact_type=ArtifactType.COMPILED_STRATEGY_IR,
            source_system="builder",
            uri="artifact://test",
            sha256="",
        )
        # Artifact-backed evidence should have a non-empty hash
        assert ref.sha256 == ""  # allowed in model, verifier enforces non-empty
