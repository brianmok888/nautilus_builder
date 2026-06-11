"""Evidence verifier — verifies evidence refs against expected constraints."""
from __future__ import annotations

from packages.evidence_ledger.models import (
    ArtifactType,
    EvidenceRef,
    VerificationStatus,
)

# Artifact types that require a non-empty SHA-256
_HASH_REQUIRED_TYPES = {
    ArtifactType.COMPILED_STRATEGY_IR,
    ArtifactType.FEATURE_DEPENDENCY_GRAPH,
    ArtifactType.RISK_CONTRACT,
    ArtifactType.REPLAY_MANIFEST,
    ArtifactType.BACKTEST_RESULT,
    ArtifactType.CATALOG_DATASET_MANIFEST,
}

_SHA256_HEX_LENGTH = 64


def verify_evidence_ref(ref: EvidenceRef) -> EvidenceRef:
    """Verify an evidence reference.

    Returns a copy with updated verification_status.
    """
    # Check hash requirement for artifact-backed types
    if ref.artifact_type in _HASH_REQUIRED_TYPES:
        if not ref.sha256:
            return ref.model_copy(update={
                "verification_status": VerificationStatus.FAILED,
                "verification_error": "Hash is empty for artifact-backed evidence",
            })
        if len(ref.sha256) != _SHA256_HEX_LENGTH:
            return ref.model_copy(update={
                "verification_status": VerificationStatus.HASH_MISMATCH,
                "verification_error": f"SHA-256 is {len(ref.sha256)} chars, expected {_SHA256_HEX_LENGTH}",
            })

    # All checks passed
    return ref.model_copy(update={
        "verification_status": VerificationStatus.VERIFIED,
        "verification_error": None,
    })
