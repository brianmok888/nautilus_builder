from packages.workflow_spine import AiSuggestionRecord, InMemoryWorkflowRepository, TestResultRecord
from services.api.app import create_app


def _repository_with_result_and_suggestion() -> InMemoryWorkflowRepository:
    repository = InMemoryWorkflowRepository()
    repository.save_result(
        TestResultRecord(
            result_id="res_001",
            test_job_id="job_001",
            project_id="project_001",
            strategy_lineage_id="lineage_alpha",
            strategy_version_id="sv_001",
            metrics={"sharpe": 1.25},
            artifact_refs={"equity_curve": "artifact://res_001/equity.parquet"},
        )
    )
    repository.save_ai_suggestion(
        AiSuggestionRecord(
            suggestion_id="sug_001",
            project_id="project_001",
            strategy_lineage_id="lineage_alpha",
            strategy_version_id="sv_001",
            result_id="res_001",
            ai_thread_id="ai_thread_001",
            improvement_cycle_id="cycle_001",
            suggestion_type="parameter_adjustment",
            message="Lower RSI threshold and retest.",
        )
    )
    return repository


def test_workflow_result_endpoint_reads_result_from_repository() -> None:
    app = create_app(workflow_repository=_repository_with_result_and_suggestion())

    response = app.get("/api/workflow/results/res_001")

    payload = response.json()
    assert response.status_code == 200
    assert payload["result_id"] == "res_001"
    assert payload["strategy_lineage_id"] == "lineage_alpha"
    assert payload["metrics"]["sharpe"] == 1.25


def test_workflow_result_suggestions_endpoint_reads_suggestions_from_repository() -> None:
    app = create_app(workflow_repository=_repository_with_result_and_suggestion())

    response = app.get("/api/workflow/results/res_001/suggestions")

    payload = response.json()
    assert response.status_code == 200
    assert payload[0]["suggestion_id"] == "sug_001"
    assert payload[0]["ai_thread_id"] == "ai_thread_001"
    assert "display_name" not in payload[0]


def test_workflow_result_endpoint_returns_404_for_unknown_result() -> None:
    app = create_app(workflow_repository=InMemoryWorkflowRepository())

    response = app.get("/api/workflow/results/missing")

    assert response.status_code == 404
    assert response.json()["error"] == "result_not_found"
