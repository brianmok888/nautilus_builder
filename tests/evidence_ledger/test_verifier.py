"""Evidence verifier tests — Segment 7."""
import pytest

from packages.evidence_ledger.models import ArtifactType, EvidenceRef, VerificationStatus
from packages.evidence_ledger.verifier import verify_evidence_ref


class TestEvidenceVerifier:
    def test_verify_unverified_becomes_verified(self) -> None:
        ref = EvidenceRef(
            evidence_id="ev_001",
            project_id="proj_001",
            artifact_type=ArtifactType.COMPILED_STRATEGY_IR,
            source_system="builder",
            uri="artifact://builder/compile/abc",
            sha256="a" * 64,
        )
        result = verify_evidence_ref(ref)
        assert result.verification_status == VerificationStatus.VERIFIED

    def test_verify_empty_hash_fails(self) -> None:
        ref = EvidenceRef(
            evidence_id="ev_002",
            project_id="proj_001",
            artifact_type=ArtifactType.COMPILED_STRATEGY_IR,
            source_system="builder",
            uri="artifact://test",
            sha256="",
        )
        result = verify_evidence_ref(ref)
        assert result.verification_status == VerificationStatus.FAILED

    def test_verify_short_hash_fails(self) -> None:
        ref = EvidenceRef(
            evidence_id="ev_003",
            project_id="proj_001",
            artifact_type=ArtifactType.COMPILED_STRATEGY_IR,
            source_system="builder",
            uri="artifact://test",
            sha256="short",
        )
        result = verify_evidence_ref(ref)
        assert result.verification_status == VerificationStatus.HASH_MISMATCH
