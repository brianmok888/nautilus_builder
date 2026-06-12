"""Tests for evidence API routes and verifier — Segment 03 v5.

Uses InMemoryEvidenceRepository through the route functions,
verifying project scoping and scoped mutations.
"""
from __future__ import annotations

from packages.evidence_ledger.in_memory_repository import InMemoryEvidenceRepository
from packages.evidence_ledger.models import EvidenceRef
from services.api.routes.evidence import (
    create_evidence,
    get_evidence,
    list_evidence_for_strategy,
    verify_evidence,
)


def _make_repo() -> InMemoryEvidenceRepository:
    return InMemoryEvidenceRepository()


def test_create_and_get_evidence() -> None:
    repo = _make_repo()
    payload = {
        "evidence_id": "ev_test_001",
        "project_id": "project_001",
        "artifact_type": "backtest_result",
        "source_system": "backtest_runner",
        "uri": "artifact://backtests/bt_001/result.json",
        "sha256": "a" * 64,
        "schema_version": "evidence_v1",
        "producer": "backtest_runner",
    }
    result = create_evidence(payload, repo=repo)
    assert result["evidence_id"] == "ev_test_001"
    assert result["verification_status"] in ("verified", "failed", "hash_mismatch")

    retrieved = get_evidence("ev_test_001", project_id="project_001", repo=repo)
    assert retrieved is not None
    assert retrieved["evidence_id"] == "ev_test_001"


def test_get_missing_evidence_returns_none() -> None:
    repo = _make_repo()
    assert get_evidence("nonexistent", project_id="project_001", repo=repo) is None


def test_get_evidence_wrong_project_returns_none() -> None:
    """Scope mismatch: requesting with wrong project returns None."""
    repo = _make_repo()
    payload = {
        "evidence_id": "ev_scope_001",
        "project_id": "project_001",
        "artifact_type": "backtest_result",
        "source_system": "backtest_runner",
        "uri": "artifact://backtests/bt_scope.json",
        "sha256": "d" * 64,
        "schema_version": "evidence_v1",
    }
    create_evidence(payload, repo=repo)
    assert get_evidence("ev_scope_001", project_id="wrong_project", repo=repo) is None


def test_verify_evidence() -> None:
    repo = _make_repo()
    payload = {
        "evidence_id": "ev_verify_001",
        "project_id": "project_001",
        "artifact_type": "compiled_strategy_ir",
        "source_system": "compiler",
        "uri": "artifact://compile/ir_001.json",
        "sha256": "b" * 64,
        "schema_version": "evidence_v1",
        "producer": "compiler",
    }
    create_evidence(payload, repo=repo)
    result = verify_evidence("ev_verify_001", project_id="project_001", repo=repo)
    assert result is not None
    assert result["verification_status"] == "verified"


def test_verify_missing_returns_none() -> None:
    repo = _make_repo()
    result = verify_evidence("nonexistent_id", project_id="project_001", repo=repo)
    assert result is None


def test_list_evidence_for_strategy() -> None:
    repo = _make_repo()
    create_evidence({
        "evidence_id": "ev_list_001",
        "project_id": "project_001",
        "artifact_type": "risk_contract",
        "source_system": "compiler",
        "uri": "artifact://risk/rc_001.json",
        "sha256": "c" * 64,
        "schema_version": "evidence_v1",
        "strategy_lineage_id": "lineage_list_test",
    }, repo=repo)
    results = list_evidence_for_strategy(
        "lineage_list_test", project_id="project_001", repo=repo
    )
    assert len(results) >= 1
    lineage_ids = [r.get("strategy_lineage_id") for r in results if r.get("strategy_lineage_id")]
    assert "lineage_list_test" in lineage_ids


def test_evidence_without_hash_fails_for_artifact_types() -> None:
    repo = _make_repo()
    payload = {
        "evidence_id": "ev_no_hash",
        "project_id": "project_001",
        "artifact_type": "feature_dependency_graph",
        "source_system": "compiler",
        "uri": "artifact://features/dep_001.json",
        "sha256": "",
        "schema_version": "evidence_v1",
    }
    result = create_evidence(payload, repo=repo)
    assert result["verification_status"] in ("failed", "hash_mismatch")
