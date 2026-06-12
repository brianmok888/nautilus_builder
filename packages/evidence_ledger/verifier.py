"""Evidence verifier — verifies evidence refs against expected constraints.

v6 enhancement: checks hex format, expiry, source system allowlist,
project scope, and actual artifact content when store is available.
Never mutates the original ref.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Protocol

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
_SHA256_HEX_PATTERN = re.compile(r"^[0-9a-f]{64}$")

_ALLOWED_SOURCE_SYSTEMS = {
    "builder",
    "nautilus_builder",
    "nautilus_daedalus",
    "data_tester",
    "exec_tester",
    "reconciliation_service",
    "manual_review",
    "backtest_runner",
    "compiler",
}


class ArtifactStoreForVerifier(Protocol):
    """Minimal protocol the verifier needs from an artifact store."""

    def get_json(self, *, artifact_ref: str, **kwargs: Any) -> Any: ...


def verify_evidence_ref(
    ref: EvidenceRef,
    *,
    artifact_store: ArtifactStoreForVerifier | None = None,
    context_project_id: str | None = None,
    now: datetime | None = None,
) -> EvidenceRef:
    """Verify an evidence reference.

    Returns a copy with updated verification_status.
    Never mutates the original ref.
    """
    _now = now or datetime.now(timezone.utc)

    # 1. Check source system
    if ref.source_system not in _ALLOWED_SOURCE_SYSTEMS:
        return ref.model_copy(update={
            "verification_status": VerificationStatus.FAILED,
            "verification_error": f"unknown source_system: {ref.source_system}",
        })

    # 2. Check project scope
    if context_project_id is not None and ref.project_id != context_project_id:
        return ref.model_copy(update={
            "verification_status": VerificationStatus.SCOPE_MISMATCH,
            "verification_error": f"project scope mismatch: ref={ref.project_id}, context={context_project_id}",
        })

    # 3. Check expiry
    if ref.expires_at is not None:
        expires_dt = ref.expires_at
        if isinstance(expires_dt, str):
            try:
                expires_dt = datetime.fromisoformat(expires_dt)
            except ValueError:
                expires_dt = None
        if expires_dt is not None and expires_dt.tzinfo is None:
            expires_dt = expires_dt.replace(tzinfo=timezone.utc)
        if expires_dt is not None and expires_dt <= _now:
            return ref.model_copy(update={
                "verification_status": VerificationStatus.EXPIRED,
                "verification_error": f"evidence expired at {ref.expires_at}",
            })

    # 4. Check hash requirement for artifact-backed types
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
        if not _SHA256_HEX_PATTERN.fullmatch(ref.sha256):
            return ref.model_copy(update={
                "verification_status": VerificationStatus.HASH_MISMATCH,
                "verification_error": "SHA-256 contains non-hex or uppercase characters",
            })

    # 5. Check actual artifact content when store is available
    if artifact_store is not None and ref.sha256:
        try:
            stored = artifact_store.get_json(artifact_ref=ref.uri)
            actual_checksum = stored.record.checksum_sha256
            if actual_checksum != ref.sha256:
                return ref.model_copy(update={
                    "verification_status": VerificationStatus.HASH_MISMATCH,
                    "verification_error": f"artifact checksum mismatch: expected={ref.sha256}, actual={actual_checksum}",
                })
        except ValueError:
            return ref.model_copy(update={
                "verification_status": VerificationStatus.FAILED,
                "verification_error": f"artifact not found or unreadable: {ref.uri}",
            })

    # All checks passed
    return ref.model_copy(update={
        "verification_status": VerificationStatus.VERIFIED,
        "verification_error": None,
    })
