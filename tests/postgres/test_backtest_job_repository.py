"""Tests for PostgresBacktestJobRepository.

Uses pytest fixtures that mock the Postgres connection.
These tests verify the repository logic without requiring a real database.
"""
from __future__ import annotations

import json
from typing import Any
from unittest.mock import MagicMock

import pytest

from packages.backtest_jobs.models import BacktestJob
from packages.postgres.backtest_job_repository import PostgresBacktestJobRepository


@pytest.fixture
def mock_conn() -> MagicMock:
    return MagicMock()


@pytest.fixture
def repo(mock_conn: MagicMock) -> PostgresBacktestJobRepository:
    return PostgresBacktestJobRepository(mock_conn)


def _make_job(**overrides: Any) -> BacktestJob:
    defaults = {
        "job_id": "bt_test001",
        "status": "CREATED",
        "stage": "CREATED",
        "created_by": "builder_api",
        "created_at": "2025-06-01T00:00:00Z",
        "updated_at": "2025-06-01T00:00:00Z",
        "strategy_spec_version_id": "strategy_001_v001",
        "adapter_profile_id": "BINANCE_PERP",
        "instrument_id": "BTCUSDT-PERP",
        "data_range": "2025-01-01:2025-06-01",
        "worker_id": "unassigned",
        "result_artifact_refs": {},
        "event_stream_id": "builder:runtime:bt_test001",
        "user_id": "system",
        "project_id": "default",
        "dataset_id": "unspecified",
        "catalog_path": None,
        "data_type": "bars",
        "timeframe": "5m",
        "market_type": "perp",
        "compile_hash": "a" * 64,
        "validation_report_id": "vr_001",
        "compile_artifact_id": None,
        "cancel_requested": False,
    }
    defaults.update(overrides)
    return BacktestJob(**defaults)


def _job_row(job: BacktestJob) -> tuple:
    """Convert a BacktestJob to a mock DB row tuple."""
    return (
        job.job_id,
        job.strategy_spec_version_id.split("_v")[0] if "_v" in job.strategy_spec_version_id else "",
        job.strategy_spec_version_id,
        job.adapter_profile_id,
        job.instrument_id,
        job.data_range,
        job.compile_hash,
        job.compile_artifact_id,
        job.validation_report_id,
        job.status,
        job.stage,
        job.status,  # lifecycle_status
        job.worker_id,
        json.dumps(job.result_artifact_refs),
        job.event_stream_id,
        job.created_by,
        job.user_id,
        job.project_id,
        job.dataset_id,
        job.catalog_path,
        job.data_type,
        job.timeframe,
        job.market_type,
        job.cancel_requested,
        job.created_at,
        job.updated_at,
    )


class TestPostgresBacktestJobRepository:
    def test_save_executes_upsert(self, repo: PostgresBacktestJobRepository, mock_conn: MagicMock) -> None:
        job = _make_job()
        repo.save(job)
        # Verify execute was called (with INSERT ... ON CONFLICT)
        mock_conn.execute.assert_called_once()
        call_args = mock_conn.execute.call_args
        assert "INSERT" in call_args[0][0]
        assert "ON CONFLICT" in call_args[0][0]

    def test_get_returns_job_when_found(self, repo: PostgresBacktestJobRepository, mock_conn: MagicMock) -> None:
        job = _make_job()
        mock_conn.execute.return_value.fetchone.return_value = _job_row(job)

        result = repo.get("bt_test001")
        assert result is not None
        assert result.job_id == "bt_test001"
        assert result.status == "CREATED"
        assert result.strategy_spec_version_id == "strategy_001_v001"

    def test_get_returns_none_when_not_found(self, repo: PostgresBacktestJobRepository, mock_conn: MagicMock) -> None:
        mock_conn.execute.return_value.fetchone.return_value = None
        result = repo.get("nonexistent")
        assert result is None

    def test_list_by_strategy_version(self, repo: PostgresBacktestJobRepository, mock_conn: MagicMock) -> None:
        job = _make_job()
        mock_conn.execute.return_value.fetchall.return_value = [_job_row(job)]

        results = repo.list_by_strategy_version("strategy_001_v001")
        assert len(results) == 1
        assert results[0].job_id == "bt_test001"

    def test_list_all(self, repo: PostgresBacktestJobRepository, mock_conn: MagicMock) -> None:
        job1 = _make_job(job_id="bt_001")
        job2 = _make_job(job_id="bt_002", strategy_spec_version_id="strategy_002_v001")
        mock_conn.execute.return_value.fetchall.return_value = [_job_row(job1), _job_row(job2)]

        results = repo.list_all()
        assert len(results) == 2

    def test_update_status(self, repo: PostgresBacktestJobRepository, mock_conn: MagicMock) -> None:
        updated_job = _make_job(status="SUCCEEDED", stage="SUCCEEDED")
        mock_conn.execute.return_value.fetchone.return_value = _job_row(updated_job)

        result = repo.update_status(
            "bt_test001",
            "SUCCEEDED",
            result_artifact_refs={"report": "report.json"},
        )
        assert result is not None
        assert result.status == "SUCCEEDED"

    def test_request_cancel(self, repo: PostgresBacktestJobRepository, mock_conn: MagicMock) -> None:
        cancelled_job = _make_job(status="CANCEL_REQUESTED", stage="CANCEL_REQUESTED", cancel_requested=True)
        mock_conn.execute.return_value.fetchone.return_value = _job_row(cancelled_job)

        result = repo.request_cancel("bt_test001")
        assert result is not None
        assert result.cancel_requested is True
        assert result.status == "CANCEL_REQUESTED"
