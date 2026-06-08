"""Tests for the read-only strategy evidence summary endpoint."""
from __future__ import annotations

import pytest

from packages.backtest_jobs.service import BacktestJobService
from packages.auth import UserProjectContext
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
    payload = strategy_evidence_summary_payload(repo, "demo_compiled")
    result = payload.json()
    assert result["strategyStatus"] == "backtested"
    assert result["compile"]["status"] == "passed_inferred"
    assert result["compile"]["hash"] is None


def test_approved_strategy_has_promotion_ready(repo: InMemoryStrategyRepository) -> None:
    payload = strategy_evidence_summary_payload(repo, "demo_promotion_requested")
    result = payload.json()
    assert result["strategyStatus"] == "approved"
    assert result["promotion"]["status"] == "ready"


def test_execution_ready_strategy_has_promotion_ready(repo: InMemoryStrategyRepository) -> None:
    payload = strategy_evidence_summary_payload(repo, "demo_promotion_ready")
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


def test_evidence_summary_filters_backtest_jobs_by_project() -> None:
    repo = InMemoryStrategyRepository()
    context = UserProjectContext(user_id="user_alpha", project_id="project_alpha")
    seed_demo_strategies(repo, context=context)
    bt_service = BacktestJobService()
    alpha_job = bt_service.create_job({
        "strategy_spec_version_id": "demo_validated_v001",
        "adapter_profile_id": "BINANCE_PERP",
        "instrument_id": "BTCUSDT-PERP",
        "compile_hash": "a" * 64,
        "validation_report_id": "vr_alpha",
        "data_range": "2025-01-01:2025-06-01",
        "user_id": "user_alpha",
        "project_id": "project_alpha",
    })
    bt_service.create_job({
        "strategy_spec_version_id": "demo_validated_v001",
        "adapter_profile_id": "BINANCE_PERP",
        "instrument_id": "ETHUSDT-PERP",
        "compile_hash": "b" * 64,
        "validation_report_id": "vr_beta",
        "data_range": "2025-01-01:2025-06-01",
        "user_id": "user_beta",
        "project_id": "project_beta",
    })

    payload = strategy_evidence_summary_payload(
        repo,
        "demo_validated",
        backtest_job_service=bt_service,
        context=context,
    )
    result = payload.json()

    assert [job["jobId"] for job in result["replay"]["jobs"]] == [alpha_job.job_id]
    assert result["compile"]["hash"] == "a" * 64


def test_compile_status_inferred_from_lifecycle_does_not_create_compile_audit(
    repo: InMemoryStrategyRepository,
) -> None:
    payload = strategy_evidence_summary_payload(repo, "demo_compiled")
    result = payload.json()

    assert result["compile"]["status"] == "passed_inferred"
    assert all(event["kind"] != "compiled" for event in result["audit"])


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


def test_evidence_summary_uses_public_service_methods_not_private_internals(
    repo: InMemoryStrategyRepository,
) -> None:
    """Verify evidence summary never directly accesses _jobs_by_id."""
    bt_service = BacktestJobService()
    version_id = "demo_validated_v001"
    job = bt_service.create_job({
        "strategy_spec_version_id": version_id,
        "adapter_profile_id": "BINANCE_PERP",
        "instrument_id": "BTCUSDT-PERP",
        "compile_hash": "b" * 64,
        "validation_report_id": "vr_pub_test",
        "data_range": "2025-01-01:2025-06-01",
    })
    bt_service.transition_job(job.job_id, "SUCCEEDED", result_artifact_refs={"report": "r.json"})

    # Verify public methods return correct data
    listed = bt_service.list_jobs_for_strategy(version_id)
    assert len(listed) == 1
    assert listed[0].job_id == job.job_id

    latest = bt_service.get_latest_job_for_strategy(version_id)
    assert latest is not None
    assert latest.job_id == job.job_id

    # Evidence summary should produce same result using public methods
    payload = strategy_evidence_summary_payload(repo, "demo_validated", backtest_job_service=bt_service)
    result = payload.json()
    assert result["replay"]["status"] == "passed"
    assert len(result["replay"]["jobs"]) == 1
    assert result["compile"]["hash"] == "b" * 64


def test_list_jobs_for_strategy_empty_when_no_jobs(
    repo: InMemoryStrategyRepository,
) -> None:
    """list_jobs_for_strategy returns empty list when no jobs exist."""
    bt_service = BacktestJobService()
    assert bt_service.list_jobs_for_strategy("nonexistent_version") == []
    assert bt_service.get_latest_job_for_strategy("nonexistent_version") is None


def test_list_jobs_for_strategy_returns_ordered_jobs(
    repo: InMemoryStrategyRepository,
) -> None:
    """list_jobs_for_strategy returns jobs in creation order."""
    bt_service = BacktestJobService()
    version_id = "demo_validated_v001"

    job_a = bt_service.create_job({
        "strategy_spec_version_id": version_id,
        "adapter_profile_id": "BINANCE_PERP",
        "instrument_id": "BTCUSDT-PERP",
        "compile_hash": "c" * 64,
        "validation_report_id": "vr_ord_1",
        "data_range": "2025-01-01:2025-06-01",
    })

    # Second job with slightly different payload to get a different key
    job_b = bt_service.create_job({
        "strategy_spec_version_id": version_id,
        "adapter_profile_id": "BINANCE_PERP",
        "instrument_id": "ETHUSDT-PERP",
        "compile_hash": "d" * 64,
        "validation_report_id": "vr_ord_2",
        "data_range": "2025-01-01:2025-06-01",
    })

    jobs = bt_service.list_jobs_for_strategy(version_id)
    assert len(jobs) == 2
    assert jobs[0].job_id == job_a.job_id
    assert jobs[1].job_id == job_b.job_id

    latest = bt_service.get_latest_job_for_strategy(version_id)
    assert latest is not None
    assert latest.job_id == job_b.job_id


def test_missing_jobs_produce_replay_missing_status(
    repo: InMemoryStrategyRepository,
) -> None:
    """When no backtest jobs exist, replay.status is missing."""
    payload = strategy_evidence_summary_payload(repo, "demo_draft")
    result = payload.json()
    assert result["replay"]["status"] == "missing"
    assert result["replay"]["jobs"] == []


def test_failed_jobs_produce_replay_failed_status(
    repo: InMemoryStrategyRepository,
) -> None:
    """When a backtest job failed, replay.status is failed."""
    bt_service = BacktestJobService()
    version_id = "demo_validated_v001"
    job = bt_service.create_job({
        "strategy_spec_version_id": version_id,
        "adapter_profile_id": "BINANCE_PERP",
        "instrument_id": "BTCUSDT-PERP",
        "compile_hash": "e" * 64,
        "validation_report_id": "vr_fail",
        "data_range": "2025-01-01:2025-06-01",
    })
    bt_service.transition_job(job.job_id, "FAILED")

    payload = strategy_evidence_summary_payload(repo, "demo_validated", backtest_job_service=bt_service)
    result = payload.json()
    assert result["replay"]["status"] == "failed"


def test_passed_jobs_produce_replay_passed_status(
    repo: InMemoryStrategyRepository,
) -> None:
    """When a backtest job succeeded, replay.status is passed."""
    bt_service = BacktestJobService()
    version_id = "demo_validated_v001"
    job = bt_service.create_job({
        "strategy_spec_version_id": version_id,
        "adapter_profile_id": "BINANCE_PERP",
        "instrument_id": "BTCUSDT-PERP",
        "compile_hash": "f" * 64,
        "validation_report_id": "vr_pass",
        "data_range": "2025-01-01:2025-06-01",
    })
    bt_service.transition_job(job.job_id, "SUCCEEDED", result_artifact_refs={"report": "r.json"})

    payload = strategy_evidence_summary_payload(repo, "demo_validated", backtest_job_service=bt_service)
    result = payload.json()
    assert result["replay"]["status"] == "passed"
