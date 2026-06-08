"""Tests for the read-only strategy evidence summary endpoint."""
from __future__ import annotations

import pytest

from packages.backtest_jobs.service import BacktestJobService
from packages.strategy_spec.demo_seed import seed_demo_strategies
from packages.strategy_spec.repository import InMemoryStrategyRepository
from services.api.routes.evidence_summary import strategy_evidence_summary_payload


@pytest.fixture
def repo() -> InMemoryStrategyRepository:
    repo = InMemoryStrategyRepository()
    seed_demo_strategies(repo)
    return repo


def test_draft_strategy_returns_missing_evidence(repo: InMemoryStrategyRepository) -> None:
    payload = strategy_evidence_summary_payload(repo, "demo_draft")
    result = payload.json()
    assert result["strategyStatus"] == "draft"
    assert result["validation"]["status"] in ("missing", "unknown", "passed")
    assert result["compile"]["status"] == "missing"
    assert result["replay"]["status"] == "missing"
    assert result["promotion"]["status"] == "missing"


def test_validated_strategy_has_validation_passed(repo: InMemoryStrategyRepository) -> None:
    payload = strategy_evidence_summary_payload(repo, "demo_validated")
    result = payload.json()
    assert result["strategyStatus"] == "validated"
    assert result["validation"]["status"] == "passed"
    assert result["compile"]["status"] == "missing"


def test_backtested_strategy_has_compile_evidence(repo: InMemoryStrategyRepository) -> None:
    payload = strategy_evidence_summary_payload(repo, "demo_backtested")
    result = payload.json()
    assert result["strategyStatus"] == "backtested"
    # Backend status "backtested" implies compile passed even without explicit hash.
    assert result["compile"]["status"] == "passed"


def test_approved_strategy_has_promotion_ready(repo: InMemoryStrategyRepository) -> None:
    payload = strategy_evidence_summary_payload(repo, "demo_approved")
    result = payload.json()
    assert result["strategyStatus"] == "approved"
    assert result["promotion"]["status"] == "ready"


def test_execution_ready_strategy_has_promotion_ready(repo: InMemoryStrategyRepository) -> None:
    payload = strategy_evidence_summary_payload(repo, "demo_execution_ready")
    result = payload.json()
    assert result["strategyStatus"] == "execution_ready"
    assert result["promotion"]["status"] == "ready"


def test_evidence_summary_includes_audit_events(repo: InMemoryStrategyRepository) -> None:
    payload = strategy_evidence_summary_payload(repo, "demo_validated")
    result = payload.json()
    audit = result["audit"]
    assert len(audit) >= 1
    # Created event always exists
    assert audit[0]["kind"] == "created"
    assert audit[0]["status"] == "info"


def test_evidence_summary_with_backtest_job(repo: InMemoryStrategyRepository) -> None:
    bt_service = BacktestJobService()
    # Create a backtest job for the validated strategy
    version_id = "demo_validated_v001"
    job = bt_service.create_job({
        "strategy_spec_version_id": version_id,
        "adapter_profile_id": "BINANCE_PERP",
        "instrument_id": "BTCUSDT-PERP",
        "compile_hash": "a" * 64,
        "validation_report_id": "vr_001",
        "data_range": "2025-01-01:2025-06-01",
    })
    bt_service.transition_job(job.job_id, "SUCCEEDED", result_artifact_refs={"report": "report.json"})

    payload = strategy_evidence_summary_payload(repo, "demo_validated", backtest_job_service=bt_service)
    result = payload.json()

    assert result["compile"]["status"] == "passed"
    assert result["compile"]["hash"] == "a" * 64
    assert result["replay"]["status"] == "passed"
    assert len(result["replay"]["jobs"]) == 1
    assert result["replay"]["jobs"][0]["jobId"] == job.job_id


def test_evidence_summary_not_found(repo: InMemoryStrategyRepository) -> None:
    payload = strategy_evidence_summary_payload(repo, "nonexistent_strategy")
    assert payload.status_code == 404


def test_evidence_summary_does_not_invent_evidence(repo: InMemoryStrategyRepository) -> None:
    payload = strategy_evidence_summary_payload(repo, "demo_draft")
    result = payload.json()
    # Draft with no backtest jobs should have missing replay
    assert result["replay"]["status"] == "missing"
    assert result["replay"]["jobs"] == []
    # No compile hash should be present
    assert result["compile"]["hash"] is None
    assert result["compile"]["artifactId"] is None
    # Audit should only have the created event
    created_events = [e for e in result["audit"] if e["kind"] == "created"]
    assert len(created_events) == 1
