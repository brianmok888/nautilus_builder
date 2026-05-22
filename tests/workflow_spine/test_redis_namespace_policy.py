import pytest

from packages.workflow_spine import InMemoryWorkflowStream, InvalidStreamNamespaceError, WorkflowEvent


def _event() -> WorkflowEvent:
    return WorkflowEvent(
        event="strategy.versioned",
        project_id="project_001",
        strategy_id="strat_001",
        strategy_lineage_id="lineage_alpha",
        strategy_version_id="sv_001",
    )


def test_builder_stream_accepts_builder_namespace() -> None:
    stream = InMemoryWorkflowStream()

    stream.publish("builder:workflow:events", _event())

    assert stream.events_for("builder:workflow:events")[0].event == "strategy.versioned"


def test_nd_internal_stream_writes_are_rejected() -> None:
    stream = InMemoryWorkflowStream()

    with pytest.raises(InvalidStreamNamespaceError, match="Builder may not write to ND-owned stream"):
        stream.publish("nd:internal:events", _event())


def test_explicit_builder_nd_bridge_streams_are_allowed() -> None:
    stream = InMemoryWorkflowStream()

    stream.publish("builder:nd:advisory", _event())
    stream.publish("builder:nd:reports", _event())

    assert len(stream.events_for("builder:nd:advisory")) == 1
    assert len(stream.events_for("builder:nd:reports")) == 1
