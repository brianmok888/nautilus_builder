"""P2-1 regression: evidence repository construction must guard production.

create_fastapi_app enforces persistent evidence storage at startup, but a worker
or CLI that constructs evidence services directly could bypass it. The factory
must reject an in-memory repository outside LOCAL mode (defense in depth).
"""
from __future__ import annotations

import pytest

from packages.auth.policy import BuilderEnvironment
from packages.evidence_ledger.in_memory_repository import InMemoryEvidenceRepository
from packages.evidence_ledger.postgres_repository import PostgresEvidenceRepository
from packages.evidence_ledger.factory import create_evidence_repository_for_env


class _FakePersistentRepo:
    """Stand-in for a non-in-memory (persistent) repository. The factory only
    checks isinstance(repo, InMemoryEvidenceRepository), so any other type is
    treated as persistent."""
    pass


def test_factory_allows_in_memory_in_local():
    repo = InMemoryEvidenceRepository()
    result = create_evidence_repository_for_env(repo, environment=BuilderEnvironment.LOCAL)
    assert result is repo


def test_factory_rejects_in_memory_in_production():
    repo = InMemoryEvidenceRepository()
    with pytest.raises(ValueError, match="(?i)persistent evidence storage"):
        create_evidence_repository_for_env(repo, environment=BuilderEnvironment.PRODUCTION)


def test_factory_rejects_in_memory_in_staging():
    repo = InMemoryEvidenceRepository()
    with pytest.raises(ValueError, match="(?i)persistent evidence storage"):
        create_evidence_repository_for_env(repo, environment=BuilderEnvironment.STAGING)


def test_factory_allows_persistent_repo_outside_local():
    pg = _FakePersistentRepo()
    # Persistent repo is fine in production/staging.
    result = create_evidence_repository_for_env(pg, environment=BuilderEnvironment.PRODUCTION)
    assert result is pg
