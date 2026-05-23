from __future__ import annotations

from packages.workflow_spine.models import TestResultRecord


def result_dashboard_payload(result: TestResultRecord) -> dict[str, object]:
    return {
        "mode": "observational",
        "result_id": result.result_id,
        "test_job_id": result.test_job_id,
        "strategy_lineage_id": result.strategy_lineage_id,
        "strategy_version_id": result.strategy_version_id,
        "metrics": result.metrics,
        "artifacts": result.artifact_refs,
        "may_submit_order": False,
    }
