from packages.workflow_spine import AiSuggestionRecord, InMemoryWorkflowRepository, WorkflowResultRecord


def test_repository_stores_results_by_result_and_job_id() -> None:
    repository = InMemoryWorkflowRepository()
    result = WorkflowResultRecord(
        result_id="res_001",
        test_job_id="job_001",
        project_id="project_001",
        strategy_lineage_id="lineage_alpha",
        strategy_version_id="sv_001",
        metrics={"sharpe": 1.25, "max_drawdown": 0.12},
        artifact_refs={"equity_curve": "artifact://res_001/equity_curve.parquet"},
    )

    repository.save_result(result)

    assert repository.result("res_001") == result
    assert repository.result_for_job("job_001") == result


def test_repository_stores_ai_suggestions_by_lineage_result_and_thread() -> None:
    repository = InMemoryWorkflowRepository()
    suggestion = AiSuggestionRecord(
        suggestion_id="sug_001",
        project_id="project_001",
        strategy_lineage_id="lineage_alpha",
        strategy_version_id="sv_001",
        result_id="res_001",
        ai_thread_id="ai_thread_001",
        improvement_cycle_id="cycle_001",
        suggestion_type="parameter_adjustment",
        message="Lower RSI exit threshold and retest drawdown.",
    )

    repository.save_ai_suggestion(suggestion)

    assert repository.suggestions_for_lineage("lineage_alpha") == [suggestion]
    assert repository.suggestions_for_result("res_001") == [suggestion]
    assert repository.suggestions_for_ai_thread("ai_thread_001") == [suggestion]


def test_ai_suggestion_storage_does_not_depend_on_display_name() -> None:
    repository = InMemoryWorkflowRepository()
    suggestion = AiSuggestionRecord(
        suggestion_id="sug_001",
        project_id="project_001",
        strategy_lineage_id="lineage_alpha",
        strategy_version_id="sv_001",
        result_id="res_001",
        ai_thread_id="ai_thread_001",
        improvement_cycle_id="cycle_001",
        suggestion_type="rename_safe_improvement",
        message="Names may change; lineage remains stable.",
    )

    repository.save_ai_suggestion(suggestion)

    payload = suggestion.model_dump(mode="json")
    assert payload["strategy_lineage_id"] == "lineage_alpha"
    assert "display_name" not in payload
