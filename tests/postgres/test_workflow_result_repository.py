"""Tests for PostgresWorkflowResultRepository."""
from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

from packages.workflow_spine.models import WorkflowResultRecord
from packages.postgres.workflow_result_repository import PostgresWorkflowResultRepository


@pytest.fixture
def mock_conn() -> MagicMock:
    return MagicMock()


@pytest.fixture
def repo(mock_conn: MagicMock) -> PostgresWorkflowResultRepository:
    return PostgresWorkflowResultRepository(mock_conn)


def _make_result(**overrides) -> WorkflowResultRecord:
    defaults = {
        "result_id": "result_001",
        "test_job_id": "job_001",
        "strategy_lineage_id": "lineage_001",
        "strategy_version_id": "strategy_001_v001",
        "project_id": "default",
        "metrics": {"sharpe": 1.5},
        "artifact_refs": {"report": "report.json"},
        "created_at": "2025-06-01T00:00:00Z",
    }
    defaults.update(overrides)
    return WorkflowResultRecord(**defaults)


def _result_row(record: WorkflowResultRecord) -> tuple:
    """Return a mock row tuple matching the repository's SELECT payload query."""
    payload = record.model_dump(mode="json")
    # The repo SELECTs only the payload column, so the row is a 1-tuple
    return (json.dumps(payload),)


class TestPostgresWorkflowResultRepository:
    def test_save_result_executes_upsert(self, repo: PostgresWorkflowResultRepository, mock_conn: MagicMock) -> None:
        record = _make_result()
        repo.save_result(record)
        mock_conn.execute.assert_called_once()
        assert "INSERT" in mock_conn.execute.call_args[0][0]
        assert "ON CONFLICT" in mock_conn.execute.call_args[0][0]

    def test_result_returns_record_when_found(self, repo: PostgresWorkflowResultRepository, mock_conn: MagicMock) -> None:
        record = _make_result()
        mock_conn.execute.return_value.fetchone.return_value = _result_row(record)

        result = repo.result("result_001")
        assert result is not None
        assert result.result_id == "result_001"

    def test_result_returns_none_when_not_found(self, repo: PostgresWorkflowResultRepository, mock_conn: MagicMock) -> None:
        mock_conn.execute.return_value.fetchone.return_value = None
        result = repo.result("nonexistent")
        assert result is None

    def test_list_results_returns_all(self, repo: PostgresWorkflowResultRepository, mock_conn: MagicMock) -> None:
        r1 = _make_result(result_id="r1")
        r2 = _make_result(result_id="r2")
        mock_conn.execute.return_value.fetchall.return_value = [_result_row(r1), _result_row(r2)]

        results = repo.list_results()
        assert len(results) == 2

    def test_list_results_with_pagination(self, repo: PostgresWorkflowResultRepository, mock_conn: MagicMock) -> None:
        mock_conn.execute.return_value.fetchall.return_value = []
        repo.list_results(limit=10, offset=5)
        # Verify the query was called (with LIMIT/OFFSET)
        call_sql = mock_conn.execute.call_args[0][0]
        assert "LIMIT" in call_sql

    def test_result_for_job(self, repo: PostgresWorkflowResultRepository, mock_conn: MagicMock) -> None:
        record = _make_result(test_job_id="job_abc")
        mock_conn.execute.return_value.fetchone.return_value = _result_row(record)

        result = repo.result_for_job("job_abc")
        assert result is not None
        assert result.test_job_id == "job_abc"

    def test_results_for_lineage(self, repo: PostgresWorkflowResultRepository, mock_conn: MagicMock) -> None:
        record = _make_result(strategy_lineage_id="lineage_xyz")
        mock_conn.execute.return_value.fetchall.return_value = [_result_row(record)]

        results = repo.results_for_lineage("lineage_xyz")
        assert len(results) == 1
        assert results[0].strategy_lineage_id == "lineage_xyz"
