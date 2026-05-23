from packages.workflow_spine import InMemoryWorkflowRepository, InMemoryWorkflowStream, StrategyTestWorkflowService


def test_strategy_test_workflow_versions_and_enqueues_with_continuity_ids() -> None:
    repository = InMemoryWorkflowRepository()
    stream = InMemoryWorkflowStream()
    service = StrategyTestWorkflowService(repository=repository, stream=stream)

    outcome = service.create_version_and_enqueue_test(
        project_id="project_001",
        display_name="EMA Pullback",
        test_type="backtest",
        instrument="BTCUSDT-PERP",
        data_source="BINANCE_PERP",
        timeframe="1-MINUTE",
        start="2025-01-01",
        end="2025-01-31",
        ai_thread_id="ai_thread_001",
        improvement_cycle_id="cycle_001",
    )

    assert outcome.strategy.strategy_lineage_id == outcome.version.strategy_lineage_id
    assert outcome.version.ai_thread_id == "ai_thread_001"
    assert outcome.version.improvement_cycle_id == "cycle_001"
    assert outcome.job.strategy_version_id == outcome.version.strategy_version_id
    assert outcome.job.test_type == "backtest"

    assert repository.strategy(outcome.strategy.strategy_id) == outcome.strategy
    assert repository.version(outcome.version.strategy_version_id) == outcome.version
    assert repository.job(outcome.job.test_job_id) == outcome.job

    workflow_events = stream.events_for("builder:workflow:events")
    test_jobs = stream.events_for("builder:test:jobs")
    assert [event.event for event in workflow_events] == ["strategy.versioned"]
    assert [event.event for event in test_jobs] == ["test.enqueued"]
    assert test_jobs[0].strategy_lineage_id == outcome.strategy.strategy_lineage_id
    assert test_jobs[0].ai_thread_id == "ai_thread_001"


def test_strategy_test_workflow_records_result_completed_event_with_lineage_ids() -> None:
    repository = InMemoryWorkflowRepository()
    stream = InMemoryWorkflowStream()
    service = StrategyTestWorkflowService(repository=repository, stream=stream)
    outcome = service.create_version_and_enqueue_test(
        project_id="project_001",
        display_name="EMA Pullback",
        test_type="backtest",
        instrument="BTCUSDT-PERP",
        data_source="BINANCE_PERP",
        timeframe="1-MINUTE",
        start="2025-01-01",
        end="2025-01-31",
        ai_thread_id="ai_thread_001",
        improvement_cycle_id="cycle_001",
    )

    result = service.record_result_completed(
        test_job_id=outcome.job.test_job_id,
        result_id="res_001",
        metrics={"sharpe": 1.25},
        artifact_refs={"report": "artifact://res_001/report.json"},
    )

    assert result.strategy_lineage_id == outcome.strategy.strategy_lineage_id
    assert result.strategy_version_id == outcome.version.strategy_version_id
    assert repository.result("res_001") == result
    result_events = stream.events_for("builder:workflow:events")
    assert [event.event for event in result_events] == ["strategy.versioned", "result.completed"]
    assert result_events[-1].test_job_id == outcome.job.test_job_id
    assert result_events[-1].result_id == "res_001"
    assert result_events[-1].strategy_lineage_id == outcome.strategy.strategy_lineage_id


def test_strategy_test_workflow_records_suggestion_created_event_with_builder_nd_boundary() -> None:
    repository = InMemoryWorkflowRepository()
    stream = InMemoryWorkflowStream()
    service = StrategyTestWorkflowService(repository=repository, stream=stream)
    outcome = service.create_version_and_enqueue_test(
        project_id="project_001",
        display_name="EMA Pullback",
        test_type="backtest",
        instrument="BTCUSDT-PERP",
        data_source="BINANCE_PERP",
        timeframe="1-MINUTE",
        start="2025-01-01",
        end="2025-01-31",
        ai_thread_id="ai_thread_001",
        improvement_cycle_id="cycle_001",
    )
    service.record_result_completed(
        test_job_id=outcome.job.test_job_id,
        result_id="res_001",
        metrics={"sharpe": 1.25},
        artifact_refs={"report": "artifact://res_001/report.json"},
    )

    suggestion = service.record_suggestion_created(
        result_id="res_001",
        suggestion_id="sug_001",
        suggestion_type="parameter_adjustment",
        message="Lower RSI exit threshold and retest drawdown.",
    )

    assert suggestion.strategy_lineage_id == outcome.strategy.strategy_lineage_id
    assert suggestion.ai_thread_id == "ai_thread_001"
    assert repository.suggestions_for_result("res_001") == [suggestion]
    workflow_events = stream.events_for("builder:workflow:events")
    assert [event.event for event in workflow_events] == [
        "strategy.versioned",
        "result.completed",
        "suggestion.created",
    ]
    assert workflow_events[-1].result_id == "res_001"
    assert workflow_events[-1].ai_thread_id == "ai_thread_001"
    assert stream.events_for("nd:advisory") == []
