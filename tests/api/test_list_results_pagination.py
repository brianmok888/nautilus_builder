"""Tests for M5: list_results API route pagination support."""
from __future__ import annotations

import pytest

from packages.workflow_spine import InMemoryWorkflowRepository
from packages.workflow_spine.models import WorkflowResultRecord


def _make_result(result_id: str) -> WorkflowResultRecord:
    return WorkflowResultRecord(
        result_id=result_id,
        test_job_id=f"job_{result_id}",
        project_id="proj_1",
        strategy_lineage_id="lineage_1",
        strategy_version_id="ver_1",
        metrics={"trade_count": 0},
        artifact_refs={},
    )


def test_list_results_payload_passes_limit_to_repository():
    """M5: list_results_payload should accept and pass limit param."""
    from services.api.routes.workflow_results import list_results_payload

    repo = InMemoryWorkflowRepository()
    for i in range(10):
        repo.save_result(_make_result(f"res_{i:03d}"))

    response = list_results_payload(repo, limit=3)
    items = response.json()
    assert len(items) == 3


def test_list_results_payload_passes_offset_to_repository():
    """M5: list_results_payload should accept and pass offset param."""
    from services.api.routes.workflow_results import list_results_payload

    repo = InMemoryWorkflowRepository()
    for i in range(10):
        repo.save_result(_make_result(f"res_{i:03d}"))

    response = list_results_payload(repo, limit=3, offset=5)
    items = response.json()
    assert len(items) == 3
    # Results are sorted by created_at; offset=5 should skip first 5
    assert items[0]["result_id"] == "res_005"


def test_list_results_payload_default_returns_all():
    """M5: without limit/offset, should return all results."""
    from services.api.routes.workflow_results import list_results_payload

    repo = InMemoryWorkflowRepository()
    for i in range(5):
        repo.save_result(_make_result(f"res_{i:03d}"))

    response = list_results_payload(repo)
    items = response.json()
    assert len(items) == 5
