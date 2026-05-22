import pytest

from packages.workflow_spine import InvalidStreamNamespaceError, WorkflowEvent
from packages.workflow_spine.nd_compat import NdAdvisoryMapper


def test_builder_event_maps_to_nd_advisory_bridge_payload_with_stable_ids() -> None:
    mapper = NdAdvisoryMapper()
    event = WorkflowEvent(
        event="test.completed",
        project_id="project_001",
        strategy_id="strat_001",
        strategy_lineage_id="lineage_alpha",
        strategy_version_id="sv_002",
        test_job_id="job_001",
        result_id="res_001",
        ai_thread_id="ai_thread_001",
        improvement_cycle_id="cycle_001",
    )

    advisory = mapper.to_advisory_request(
        event,
        source_ref="nd://strategies/existing-alpha",
        display_name="AI renamed strategy label",
    )

    assert advisory.stream_name == "builder:nd:advisory"
    assert advisory.payload["strategy_lineage_id"] == "lineage_alpha"
    assert advisory.payload["strategy_version_id"] == "sv_002"
    assert advisory.payload["ai_thread_id"] == "ai_thread_001"
    assert advisory.payload["improvement_cycle_id"] == "cycle_001"
    assert advisory.payload["source_ref"] == "nd://strategies/existing-alpha"
    assert advisory.payload["display_name"] == "AI renamed strategy label"


def test_nd_advisory_mapping_continuity_does_not_require_display_name() -> None:
    mapper = NdAdvisoryMapper()
    event = WorkflowEvent(
        event="test.completed",
        project_id="project_001",
        strategy_id="strat_001",
        strategy_lineage_id="lineage_alpha",
        strategy_version_id="sv_002",
    )

    advisory = mapper.to_advisory_request(event)

    assert advisory.payload["strategy_lineage_id"] == "lineage_alpha"
    assert "display_name" not in advisory.payload


def test_nd_mapper_rejects_nd_owned_output_streams() -> None:
    mapper = NdAdvisoryMapper(output_stream="nd:ai:pipeline")
    event = WorkflowEvent(
        event="test.completed",
        project_id="project_001",
        strategy_id="strat_001",
        strategy_lineage_id="lineage_alpha",
        strategy_version_id="sv_002",
    )

    with pytest.raises(InvalidStreamNamespaceError, match="Builder may not write to ND-owned stream"):
        mapper.to_advisory_request(event)
