from packages.workflow_spine import AiSuggestionRecord, InMemoryWorkflowRepository, WorkflowResultRecord
from services.api.app import create_app


def test_result_dashboard_payload_includes_metrics_artifacts_trades_fills_and_logs() -> None:
    repo = _repository_with_result_and_suggestion()
    response = create_app(workflow_repository=repo).get("/api/results/res_001")

    assert response.status_code == 200
    assert response.json()["result_id"] == "res_001"
    assert "metrics" in response.json()
    assert "artifacts" in response.json()
    assert "trades" in response.json()
    assert "fills" in response.json()
    assert "logs" in response.json()


def test_result_dashboard_payload_includes_report_summary_for_rich_ui() -> None:
    repo = _repository_with_result_and_suggestion()
    response = create_app(workflow_repository=repo).get("/api/results/res_001")

    payload = response.json()
    assert response.status_code == 200
    assert payload["report_summary"]["sections"] == ["summary", "artifacts"]
    assert payload["report_summary"]["chart_sections"] == []
    assert payload["report_summary"]["metrics"]["trade_count"] == 0
    assert payload["report_summary"]["live_trading_enabled"] is False
    assert payload["report_summary"]["execution_authority"] is False


def _repository_with_result_and_suggestion() -> InMemoryWorkflowRepository:
    repository = InMemoryWorkflowRepository()
    repository.save_result(
        WorkflowResultRecord(
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


def test_workflow_lineage_status_endpoint_returns_read_projection() -> None:
    app = create_app(workflow_repository=_repository_with_result_and_suggestion())

    response = app.get("/api/workflow/lineages/lineage_alpha/status")

    payload = response.json()
    assert response.status_code == 200
    assert payload["strategy_lineage_id"] == "lineage_alpha"
    assert payload["strategy_version_id"] == "sv_001"
    assert payload["result_id"] == "res_001"
    assert payload["suggestion_created"] is True
    assert "display_name" not in payload


def test_result_dashboard_uses_repository_result_not_fixture() -> None:
    repo = _repository_with_result_and_suggestion()
    response = create_app(workflow_repository=repo).get("/api/results/res_001")

    payload = response.json()
    assert payload["evidence_mode"] == "repository_result"
    assert payload["artifacts"]["result"].startswith("artifact://")


def test_result_dashboard_does_not_synthesize_strategy_version_artifact() -> None:
    repo = _repository_with_result_and_suggestion()
    response = create_app(workflow_repository=repo).get("/api/results/res_001")

    payload = response.json()
    assert response.status_code == 200
    assert payload["strategy_version_id"] == "sv_001"
    assert "strategy_version_id" not in payload["artifacts"]
    assert "strategy_001_v001" not in payload["artifacts"].values()


def test_result_returns_404_when_not_in_repository() -> None:
    """Missing results return 404 (fixture fallback removed)."""
    app = create_app()

    response = app.get("/api/results/res_001")
    assert response.status_code == 404
    assert response.json()["error"] == "result_not_found"


def test_result_returns_404_for_missing_id_without_fixture_fallback() -> None:
    """Fixture fallback is removed; missing IDs always return 404."""
    app = create_app()

    response = app.get("/api/results/nonexistent_result")
    assert response.status_code == 404
    assert response.json()["error"] == "result_not_found"
