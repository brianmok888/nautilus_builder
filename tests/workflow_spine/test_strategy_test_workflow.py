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
