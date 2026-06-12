"""Tests for PostgresEvidenceRepository model/repository alignment — Segment 02 v5.

Verifies that:
- The repository imports without error (models are aligned).
- Column names match the EvidenceRef model fields.
- The repository can save, get, list, and update evidence refs.
- Scope mismatch returns None (not another project's evidence).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from unittest.mock import MagicMock

import pytest

from packages.evidence_ledger.models import (
    ArtifactType,
    EvidenceRef,
    VerificationStatus,
)
from packages.evidence_ledger.postgres_repository import PostgresEvidenceRepository


def _make_ref(**overrides: Any) -> EvidenceRef:
    defaults = {
        "evidence_id": "ev-001",
        "project_id": "proj-A",
        "strategy_lineage_id": "strat-lineage-1",
        "strategy_version_id": "strat-v1",
        "artifact_type": ArtifactType.STRATEGY_SPEC,
        "source_system": "builder",
        "uri": "s3://bucket/evidence/ev-001.json",
        "sha256": "abc123",
        "schema_version": "evidence_v1",
        "created_at": datetime(2026, 6, 11, 12, 0, 0, tzinfo=timezone.utc),
        "producer": "builder",
        "status": "active",
        "verification_status": VerificationStatus.UNVERIFIED,
        "metadata": {"test": True},
    }
    defaults.update(overrides)
    return EvidenceRef(**defaults)


class _FakeCursor:
    """Fake psycopg cursor that records queries and returns stub data."""

    def __init__(self) -> None:
        self.queries: list[str] = []
        self._results: list[list[tuple]] = []
        self.rowcount = 0

    def execute(self, query: str, params: list | None = None) -> "_FakeCursor":
        self.queries.append(query)
        return self

    def fetchone(self) -> tuple | None:
        if self._results and self._results[0]:
            return self._results.pop(0)[0]
        return None

    def fetchall(self) -> list[tuple]:
        if self._results:
            return self._results.pop(0)
        return []

    def set_results(self, *batches: list[tuple]) -> None:
        self._results = list(batches)


class _FakeConn:
    """Fake connection that returns a fake cursor."""

    def __init__(self) -> None:
        self.cursor = _FakeCursor()

    def execute(self, query: str, params: list | None = None) -> _FakeCursor:
        return self.cursor.execute(query, params)


class TestPostgresEvidenceRepositoryImport:
    """Verify the module imports and model fields align."""

    def test_imports_without_error(self) -> None:
        """Must import without ImportError from stale field names."""
        from packages.evidence_ledger.postgres_repository import (
            PostgresEvidenceRepository,
        )

        assert PostgresEvidenceRepository is not None

    def test_model_fields_match_repository_columns(self) -> None:
        """EvidenceRef model fields must be a superset of repository columns."""
        ref = _make_ref()
        model_fields = set(EvidenceRef.model_fields.keys())
        # These must exist on the model
        required = {
            "evidence_id", "project_id", "strategy_lineage_id",
            "strategy_version_id", "artifact_type", "source_system",
            "uri", "sha256", "schema_version", "producer",
            "verification_status", "verification_error",
        }
        missing = required - model_fields
        assert not missing, f"EvidenceRef model missing fields: {missing}"


class TestPostgresEvidenceRepositorySaveAndGet:
    """Verify save and get operations with model-aligned fields."""

    def test_save_inserts_model_fields(self) -> None:
        conn = _FakeConn()
        repo = PostgresEvidenceRepository(conn, schema="test")
        ref = _make_ref()
        # Clear table creation queries
        conn.cursor.queries.clear()

        result = repo.save(ref)
        assert result.evidence_id == "ev-001"

        # The INSERT query should reference model-aligned columns
        insert_queries = [q for q in conn.cursor.queries if "INSERT" in q]
        assert len(insert_queries) == 1
        insert_sql = insert_queries[0]
        assert "strategy_lineage_id" in insert_sql
        assert "source_system" in insert_sql
        assert "uri" in insert_sql

    def test_get_returns_none_for_missing(self) -> None:
        conn = _FakeConn()
        repo = PostgresEvidenceRepository(conn, schema="test")
        result = repo.get("nonexistent", "proj-A")
        assert result is None

    def test_get_returns_ref_for_match(self) -> None:
        conn = _FakeConn()
        repo = PostgresEvidenceRepository(conn, schema="test")
        ref = _make_ref()

        # Set up the fake to return a matching row
        row = (
            ref.evidence_id, ref.project_id, ref.strategy_lineage_id,
            ref.strategy_version_id, ref.artifact_type.value,
            ref.source_system, ref.uri, ref.sha256, ref.schema_version,
            ref.created_at.isoformat(), ref.producer, ref.status,
            ref.verification_status.value, ref.verification_error,
            None, ref.metadata,
        )
        conn.cursor._results = [[row]]

        result = repo.get("ev-001", "proj-A")
        assert result is not None
        assert result.evidence_id == "ev-001"
        assert result.project_id == "proj-A"
        assert result.uri == "s3://bucket/evidence/ev-001.json"

    def test_get_returns_none_for_wrong_project(self) -> None:
        """Scope mismatch: requesting with wrong project returns None."""
        conn = _FakeConn()
        repo = PostgresEvidenceRepository(conn, schema="test")
        conn.cursor._results = [[]]  # Empty result
        result = repo.get("ev-001", "wrong-project")
        assert result is None


class TestPostgresEvidenceRepositoryList:
    """Verify list operations."""

    def test_list_by_project_returns_empty(self) -> None:
        conn = _FakeConn()
        repo = PostgresEvidenceRepository(conn, schema="test")
        conn.cursor._results = [[]]
        result = repo.list_by_project("proj-A")
        assert result == []

    def test_list_by_strategy_lineage_filters(self) -> None:
        conn = _FakeConn()
        repo = PostgresEvidenceRepository(conn, schema="test")
        conn.cursor._results = [[]]
        result = repo.list_by_strategy_lineage("proj-A", "lineage-1")
        assert result == []
        # Verify the query includes strategy_lineage_id filter
        queries = conn.cursor.queries
        lineage_queries = [q for q in queries if "strategy_lineage_id" in q]
        assert len(lineage_queries) >= 1


class TestPostgresEvidenceRepositoryUpdate:
    """Verify verification status updates."""

    def test_update_verification_returns_none_if_not_found(self) -> None:
        conn = _FakeConn()
        repo = PostgresEvidenceRepository(conn, schema="test")
        conn.cursor.rowcount = 0
        result = repo.update_verification(
            "nonexistent", "proj-A", VerificationStatus.VERIFIED
        )
        assert result is None

    def test_update_verification_returns_ref_on_success(self) -> None:
        conn = _FakeConn()
        repo = PostgresEvidenceRepository(conn, schema="test")

        # First call: UPDATE returns rowcount=1
        # Second call: get returns the ref
        ref = _make_ref()
        row = (
            ref.evidence_id, ref.project_id, ref.strategy_lineage_id,
            ref.strategy_version_id, ref.artifact_type.value,
            ref.source_system, ref.uri, ref.sha256, ref.schema_version,
            ref.created_at.isoformat(), ref.producer, ref.status,
            VerificationStatus.VERIFIED.value, ref.verification_error,
            None, ref.metadata,
        )
        conn.cursor.rowcount = 1
        conn.cursor._results = [[row]]

        result = repo.update_verification(
            "ev-001", "proj-A", VerificationStatus.VERIFIED
        )
        assert result is not None
        assert result.verification_status == VerificationStatus.VERIFIED
