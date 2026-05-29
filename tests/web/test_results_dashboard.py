from __future__ import annotations

from packages.ui_contracts.results_dashboard import result_dashboard_payload
from packages.workflow_spine import WorkflowResultRecord


def test_results_dashboard_displays_metrics_and_artifacts_as_observational_data() -> None:
    result = WorkflowResultRecord(
        result_id="res_001",
        test_job_id="job_001",
        project_id="project_001",
        strategy_lineage_id="lineage_001",
        strategy_version_id="sv_001",
        metrics={"sharpe": 1.25, "max_drawdown": 0.12},
        artifact_refs={"equity_curve": "artifact://res_001/equity.parquet"},
    )

    payload = result_dashboard_payload(result)

    assert payload["mode"] == "observational"
    assert payload["result_id"] == "res_001"
    assert payload["metrics"]["sharpe"] == 1.25
    assert payload["artifacts"]["equity_curve"].startswith("artifact://")
    assert payload["may_submit_order"] is False
