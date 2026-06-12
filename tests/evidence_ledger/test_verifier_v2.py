"""Tests for enhanced evidence verifier — v6 Segment 04.

Verifies: hex format, expiry, source system allowlist, project scope,
hash mismatch from artifact store, and immutability of original ref.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import pytest

from packages.evidence_ledger.models import (
    ArtifactType,
    EvidenceRef,
    VerificationStatus,
)
from packages.evidence_ledger.verifier import verify_evidence_ref


def _make_ref(
    *,
    evidence_id: str = "ev-001",
    project_id: str = "proj-1",
    artifact_type: ArtifactType = ArtifactType.COMPILED_STRATEGY_IR,
    sha256: str = "a" * 64,
    source_system: str = "builder",
    expires_at: datetime | None = None,
    verification_status: VerificationStatus = VerificationStatus.UNVERIFIED,
) -> EvidenceRef:
    return EvidenceRef(
        evidence_id=evidence_id,
        project_id=project_id,
        artifact_type=artifact_type,
        source_system=source_system,
        uri=f"artifact://ref/{evidence_id}",
        sha256=sha256,
        verification_status=verification_status,
        expires_at=expires_at,
    )


class TestVerifierHashFormat:
    def test_valid_hex_hash_passes(self):
        ref = _make_ref(sha256="a" * 64)
        result = verify_evidence_ref(ref)
        assert result.verification_status == VerificationStatus.VERIFIED

    def test_short_hash_returns_hash_mismatch(self):
        ref = _make_ref(sha256="abc123")
        result = verify_evidence_ref(ref)
        assert result.verification_status == VerificationStatus.HASH_MISMATCH

    def test_empty_hash_for_artifact_type_returns_failed(self):
        ref = _make_ref(sha256="", artifact_type=ArtifactType.BACKTEST_RESULT)
        result = verify_evidence_ref(ref)
        assert result.verification_status == VerificationStatus.FAILED

    def test_non_hex_characters_in_hash_returns_hash_mismatch(self):
        ref = _make_ref(sha256="g" * 64)
        result = verify_evidence_ref(ref)
        assert result.verification_status == VerificationStatus.HASH_MISMATCH

    def test_uppercase_hex_returns_hash_mismatch(self):
        ref = _make_ref(sha256="A" * 64)
        result = verify_evidence_ref(ref)
        assert result.verification_status == VerificationStatus.HASH_MISMATCH

    def test_non_artifact_type_without_hash_passes(self):
        """Non-artifact-backed types (e.g., manual_review) don't need hash."""
        ref = _make_ref(
            sha256="",
            artifact_type=ArtifactType.MANUAL_REVIEW,
        )
        result = verify_evidence_ref(ref)
        assert result.verification_status == VerificationStatus.VERIFIED


class TestVerifierExpiry:
    def test_expired_evidence_returns_expired(self):
        past = datetime.now(timezone.utc) - timedelta(hours=1)
        ref = _make_ref(expires_at=past)
        result = verify_evidence_ref(ref)
        assert result.verification_status == VerificationStatus.EXPIRED

    def test_future_expiry_passes(self):
        future = datetime.now(timezone.utc) + timedelta(hours=24)
        ref = _make_ref(expires_at=future)
        result = verify_evidence_ref(ref)
        assert result.verification_status == VerificationStatus.VERIFIED

    def test_no_expiry_passes(self):
        ref = _make_ref(expires_at=None)
        result = verify_evidence_ref(ref)
        assert result.verification_status == VerificationStatus.VERIFIED


class TestVerifierSourceSystem:
    def test_known_source_system_passes(self):
        for source in ["builder", "nautilus_builder", "backtest_runner", "data_tester"]:
            ref = _make_ref(source_system=source)
            result = verify_evidence_ref(ref)
            assert result.verification_status == VerificationStatus.VERIFIED, f"Failed for {source}"

    def test_unknown_source_system_returns_failed(self):
        ref = _make_ref(source_system="unknown_attacker")
        result = verify_evidence_ref(ref)
        assert result.verification_status == VerificationStatus.FAILED


class TestVerifierProjectScope:
    def test_scope_mismatch_detected(self):
        ref = _make_ref(project_id="proj-1")
        result = verify_evidence_ref(
            ref,
            context_project_id="proj-2",
        )
        assert result.verification_status == VerificationStatus.SCOPE_MISMATCH

    def test_same_project_passes(self):
        ref = _make_ref(project_id="proj-1")
        result = verify_evidence_ref(
            ref,
            context_project_id="proj-1",
        )
        assert result.verification_status == VerificationStatus.VERIFIED

    def test_no_context_project_passes(self):
        ref = _make_ref(project_id="proj-1")
        result = verify_evidence_ref(ref)
        assert result.verification_status == VerificationStatus.VERIFIED


class TestVerifierImmutability:
    def test_verifier_does_not_mutate_original(self):
        ref = _make_ref()
        original_status = ref.verification_status
        _ = verify_evidence_ref(ref)
        assert ref.verification_status == original_status


class TestVerifierArtifactStoreChecksum:
    def test_artifact_checksum_match_returns_verified(self):
        ref = _make_ref(sha256="a" * 64)
        fake_store = _FakeArtifactStore(expected_checksum="a" * 64)
        result = verify_evidence_ref(ref, artifact_store=fake_store)
        assert result.verification_status == VerificationStatus.VERIFIED

    def test_artifact_checksum_mismatch_returns_hash_mismatch(self):
        ref = _make_ref(sha256="a" * 64)
        fake_store = _FakeArtifactStore(expected_checksum="b" * 64)
        result = verify_evidence_ref(ref, artifact_store=fake_store)
        assert result.verification_status == VerificationStatus.HASH_MISMATCH

    def test_artifact_not_found_returns_failed(self):
        ref = _make_ref(sha256="a" * 64)
        fake_store = _FakeArtifactStore(raise_not_found=True)
        result = verify_evidence_ref(ref, artifact_store=fake_store)
        assert result.verification_status == VerificationStatus.FAILED


class _FakeArtifactStore:
    """Fake artifact store for testing verifier integration."""

    def __init__(
        self,
        expected_checksum: str = "a" * 64,
        raise_not_found: bool = False,
    ) -> None:
        self._checksum = expected_checksum
        self._raise_not_found = raise_not_found

    def get_json(self, *, artifact_ref: str, **kwargs: Any) -> Any:
        if self._raise_not_found:
            raise ValueError(f"artifact not found: {artifact_ref}")
        from packages.artifact_store.models import ArtifactRecord, StoredJsonArtifact
        record = ArtifactRecord(
            artifact_ref=artifact_ref,
            artifact_type="test",
            artifact_id="test",
            user_id="u1",
            project_id="proj-1",
            path="test/path",
            checksum_sha256=self._checksum,
            created_at="2026-01-01T00:00:00Z",
        )
        return StoredJsonArtifact(record=record, payload={"test": True})
