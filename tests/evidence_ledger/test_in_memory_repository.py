"""Tests for InMemoryEvidenceRepository — model alignment, pagination, update_verification."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from packages.evidence_ledger.in_memory_repository import InMemoryEvidenceRepository
from packages.evidence_ledger.models import (
    ArtifactType,
    EvidenceRef,
    VerificationStatus,
)


def _make_ref(
    evidence_id: str = "ev-001",
    project_id: str = "proj-1",
    strategy_lineage_id: str | None = "lineage-1",
    sha256: str = "",
    artifact_type: ArtifactType = ArtifactType.STRATEGY_SPEC,
    source_system: str = "builder",
    verification_status: VerificationStatus = VerificationStatus.UNVERIFIED,
    metadata: dict | None = None,
) -> EvidenceRef:
    return EvidenceRef(
        evidence_id=evidence_id,
        project_id=project_id,
        strategy_lineage_id=strategy_lineage_id,
        artifact_type=artifact_type,
        source_system=source_system,
        uri=f"artifact://ref/{evidence_id}",
        sha256=sha256,
        verification_status=verification_status,
        metadata=metadata or {},
    )


class TestInMemoryRepositoryModuleImport:
    def test_import_succeeds(self):
        from packages.evidence_ledger.in_memory_repository import InMemoryEvidenceRepository
        assert InMemoryEvidenceRepository is not None


class TestInMemoryRepositorySaveAndGet:
    def test_save_returns_model_aligned_evidence_ref(self):
        repo = InMemoryEvidenceRepository()
        ref = _make_ref()
        saved = repo.save(ref)
        assert saved.evidence_id == "ev-001"
        assert saved.project_id == "proj-1"

    def test_get_by_project_returns_ref(self):
        repo = InMemoryEvidenceRepository()
        repo.save(_make_ref(evidence_id="ev-001", project_id="proj-1"))
        result = repo.get("ev-001", "proj-1")
        assert result is not None
        assert result.evidence_id == "ev-001"

    def test_get_wrong_project_returns_none(self):
        repo = InMemoryEvidenceRepository()
        repo.save(_make_ref(evidence_id="ev-001", project_id="proj-1"))
        assert repo.get("ev-001", "proj-2") is None


class TestInMemoryRepositoryListByProject:
    def test_list_by_project_returns_project_refs_only(self):
        repo = InMemoryEvidenceRepository()
        repo.save(_make_ref(evidence_id="ev-001", project_id="proj-1"))
        repo.save(_make_ref(evidence_id="ev-002", project_id="proj-2"))
        results = repo.list_by_project("proj-1")
        assert len(results) == 1
        assert results[0].evidence_id == "ev-001"

    def test_list_by_project_with_limit_and_offset(self):
        repo = InMemoryEvidenceRepository()
        for i in range(5):
            repo.save(_make_ref(evidence_id=f"ev-{i:03d}", project_id="proj-1"))
        results = repo.list_by_project("proj-1", limit=2, offset=1)
        assert len(results) == 2

    def test_list_by_project_default_limit_returns_all(self):
        repo = InMemoryEvidenceRepository()
        for i in range(3):
            repo.save(_make_ref(evidence_id=f"ev-{i:03d}", project_id="proj-1"))
        results = repo.list_by_project("proj-1")
        assert len(results) == 3


class TestInMemoryRepositoryListByStrategyLineage:
    def test_list_by_strategy_lineage_filters_project_and_lineage(self):
        repo = InMemoryEvidenceRepository()
        repo.save(_make_ref(evidence_id="ev-001", project_id="proj-1", strategy_lineage_id="lin-1"))
        repo.save(_make_ref(evidence_id="ev-002", project_id="proj-1", strategy_lineage_id="lin-2"))
        repo.save(_make_ref(evidence_id="ev-003", project_id="proj-2", strategy_lineage_id="lin-1"))
        results = repo.list_by_strategy_lineage("proj-1", "lin-1")
        assert len(results) == 1
        assert results[0].evidence_id == "ev-001"


class TestInMemoryRepositoryUpdateVerification:
    def test_update_verification_returns_updated_ref(self):
        repo = InMemoryEvidenceRepository()
        repo.save(_make_ref(evidence_id="ev-001", project_id="proj-1"))
        result = repo.update_verification(
            evidence_id="ev-001",
            project_id="proj-1",
            verification_status=VerificationStatus.VERIFIED,
        )
        assert result is not None
        assert result.verification_status == VerificationStatus.VERIFIED

    def test_update_verification_with_error(self):
        repo = InMemoryEvidenceRepository()
        repo.save(_make_ref(evidence_id="ev-001", project_id="proj-1"))
        result = repo.update_verification(
            evidence_id="ev-001",
            project_id="proj-1",
            verification_status=VerificationStatus.FAILED,
            error="checksum mismatch",
        )
        assert result is not None
        assert result.verification_status == VerificationStatus.FAILED
        assert result.verification_error == "checksum mismatch"

    def test_update_verification_wrong_project_returns_none(self):
        repo = InMemoryEvidenceRepository()
        repo.save(_make_ref(evidence_id="ev-001", project_id="proj-1"))
        result = repo.update_verification(
            evidence_id="ev-001",
            project_id="proj-2",
            verification_status=VerificationStatus.VERIFIED,
        )
        assert result is None

    def test_update_verification_nonexistent_returns_none(self):
        repo = InMemoryEvidenceRepository()
        result = repo.update_verification(
            evidence_id="ev-999",
            project_id="proj-1",
            verification_status=VerificationStatus.VERIFIED,
        )
        assert result is None


class TestInMemoryRepositoryRoundTrips:
    def test_enum_round_trip(self):
        repo = InMemoryEvidenceRepository()
        ref = _make_ref(verification_status=VerificationStatus.EXPIRED)
        repo.save(ref)
        result = repo.get("ev-001", "proj-1")
        assert result is not None
        assert result.verification_status == VerificationStatus.EXPIRED

    def test_datetime_round_trip(self):
        repo = InMemoryEvidenceRepository()
        now = datetime(2026, 6, 12, 12, 0, 0, tzinfo=timezone.utc)
        ref = _make_ref()
        ref = ref.model_copy(update={"created_at": now, "expires_at": now})
        saved = repo.save(ref)
        assert saved.created_at == now
        assert saved.expires_at == now

    def test_metadata_round_trip(self):
        repo = InMemoryEvidenceRepository()
        ref = _make_ref(metadata={"key": "value", "nested": {"a": 1}})
        saved = repo.save(ref)
        assert saved.metadata == {"key": "value", "nested": {"a": 1}}

    def test_metadata_none_returns_empty_dict(self):
        repo = InMemoryEvidenceRepository()
        ref = _make_ref()
        # metadata defaults to {} per model
        saved = repo.save(ref)
        assert saved.metadata == {}
