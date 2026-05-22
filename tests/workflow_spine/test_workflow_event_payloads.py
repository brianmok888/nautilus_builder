from packages.workflow_spine import WorkflowEvent


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
