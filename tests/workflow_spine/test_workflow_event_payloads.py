from packages.workflow_spine import WorkflowEvent
from packages.workflow_spine.projections import WorkflowReadModel


def test_workflow_event_carries_postgres_identity_ids() -> None:
    event = WorkflowEvent(
        event="test.completed",
        project_id="project_001",
        strategy_id="strat_001",
        strategy_lineage_id="lineage_alpha",
        strategy_version_id="sv_001",
        test_job_id="job_001",
        result_id="result_001",
        ai_thread_id="ai_thread_001",
        improvement_cycle_id="cycle_001",
    )

    payload = event.to_stream_payload()

    assert payload["event"] == "test.completed"
    assert payload["strategy_lineage_id"] == "lineage_alpha"
    assert payload["strategy_version_id"] == "sv_001"
    assert payload["result_id"] == "result_001"
    assert "display_name" not in payload


def test_workflow_read_model_projects_result_and_suggestion_status_by_lineage() -> None:
    read_model = WorkflowReadModel()
    read_model.apply(
        WorkflowEvent(
            event="strategy.versioned",
            project_id="project_001",
            strategy_id="strat_001",
            strategy_lineage_id="lineage_alpha",
            strategy_version_id="sv_001",
            ai_thread_id="ai_thread_001",
            improvement_cycle_id="cycle_001",
        )
    )
    read_model.apply(
        WorkflowEvent(
            event="test.enqueued",
            project_id="project_001",
            strategy_lineage_id="lineage_alpha",
            strategy_version_id="sv_001",
            test_job_id="job_001",
            ai_thread_id="ai_thread_001",
            improvement_cycle_id="cycle_001",
        )
    )
    read_model.apply(
        WorkflowEvent(
            event="result.completed",
            project_id="project_001",
            strategy_lineage_id="lineage_alpha",
            strategy_version_id="sv_001",
            test_job_id="job_001",
            result_id="res_001",
        )
    )
    read_model.apply(
        WorkflowEvent(
            event="suggestion.created",
            project_id="project_001",
            strategy_lineage_id="lineage_alpha",
            strategy_version_id="sv_001",
            result_id="res_001",
            ai_thread_id="ai_thread_001",
            improvement_cycle_id="cycle_001",
        )
    )

    payload = read_model.lineage_status("lineage_alpha")

    assert payload == {
        "project_id": "project_001",
        "strategy_id": "strat_001",
        "strategy_lineage_id": "lineage_alpha",
        "strategy_version_id": "sv_001",
        "test_job_id": "job_001",
        "result_id": "res_001",
        "ai_thread_id": "ai_thread_001",
        "improvement_cycle_id": "cycle_001",
        "latest_event": "suggestion.created",
        "result_completed": True,
        "suggestion_created": True,
    }


def test_workflow_read_model_rejects_events_without_lineage_id() -> None:
    read_model = WorkflowReadModel()

    try:
        read_model.apply(WorkflowEvent(event="result.completed", project_id="project_001", result_id="res_001"))
    except ValueError as exc:
        assert "workflow projection requires strategy_lineage_id" in str(exc)
    else:
        raise AssertionError("read model accepted a lineage-less workflow event")
