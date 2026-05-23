from __future__ import annotations

from packages.workflow_spine.models import WorkflowEvent


class WorkflowReadModel:
    def __init__(self) -> None:
        self._lineages: dict[str, dict[str, object]] = {}

    def apply(self, event: WorkflowEvent) -> None:
        if event.strategy_lineage_id is None:
            raise ValueError("workflow projection requires strategy_lineage_id")
        payload = event.to_stream_payload()
        state = self._lineages.setdefault(event.strategy_lineage_id, {"strategy_lineage_id": event.strategy_lineage_id})
        for key in (
            "project_id",
            "strategy_id",
            "strategy_version_id",
            "test_job_id",
            "result_id",
            "ai_thread_id",
            "improvement_cycle_id",
        ):
            if key in payload:
                state[key] = payload[key]
        state["latest_event"] = event.event
        if event.event == "result.completed":
            state["result_completed"] = True
        if event.event == "suggestion.created":
            state["suggestion_created"] = True

    def lineage_status(self, strategy_lineage_id: str) -> dict[str, object]:
        state = self._lineages.get(strategy_lineage_id)
        if state is None:
            raise KeyError(strategy_lineage_id)
        return {
            "project_id": state.get("project_id"),
            "strategy_id": state.get("strategy_id"),
            "strategy_lineage_id": strategy_lineage_id,
            "strategy_version_id": state.get("strategy_version_id"),
            "test_job_id": state.get("test_job_id"),
            "result_id": state.get("result_id"),
            "ai_thread_id": state.get("ai_thread_id"),
            "improvement_cycle_id": state.get("improvement_cycle_id"),
            "latest_event": state.get("latest_event"),
            "result_completed": bool(state.get("result_completed", False)),
            "suggestion_created": bool(state.get("suggestion_created", False)),
        }
