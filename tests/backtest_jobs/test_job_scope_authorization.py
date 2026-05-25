from __future__ import annotations

import pytest

from packages.auth import ProjectScopeError, UserProjectContext
from packages.backtest_jobs.service import BacktestJobService


def test_backtest_job_service_allows_same_scope_access() -> None:
    service = BacktestJobService()
    context = UserProjectContext(user_id="user_123", project_id="project_alpha")
    job = service.create_job(
        {
            "strategy_spec_version": "0.1.0-draft.1",
            "adapter_id": "BINANCE_PERP",
            "instrument_id": "BTCUSDT-PERP",
            "compile_hash": "abc123",
            "validation_report_id": "vr_001",
            "user_id": context.user_id,
            "project_id": context.project_id,
        }
    )

    assert service.get_job(job.job_id, context=context).job_id == job.job_id


def test_backtest_job_service_rejects_cross_project_access() -> None:
    service = BacktestJobService()
    owner = UserProjectContext(user_id="user_123", project_id="project_alpha")
    intruder = UserProjectContext(user_id="user_123", project_id="project_beta")
    job = service.create_job(
        {
            "strategy_spec_version": "0.1.0-draft.1",
            "adapter_id": "BINANCE_PERP",
            "instrument_id": "BTCUSDT-PERP",
            "compile_hash": "abc123",
            "validation_report_id": "vr_001",
            "user_id": owner.user_id,
            "project_id": owner.project_id,
        }
    )

    with pytest.raises(ProjectScopeError, match="outside user/project scope"):
        service.get_job(job.job_id, context=intruder)

    with pytest.raises(ProjectScopeError, match="outside user/project scope"):
        service.request_cancel(job.job_id, context=intruder)
