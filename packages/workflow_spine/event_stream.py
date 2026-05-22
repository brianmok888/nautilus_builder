from __future__ import annotations

from collections import defaultdict

from packages.workflow_spine.models import WorkflowEvent


class InvalidStreamNamespaceError(ValueError):
    pass


class InMemoryWorkflowStream:
    _allowed_bridge_streams = {"builder:nd:advisory", "builder:nd:reports"}

    def __init__(self) -> None:
        self._events: dict[str, list[WorkflowEvent]] = defaultdict(list)

    def publish(self, stream_name: str, event: WorkflowEvent) -> None:
        self._validate_stream_name(stream_name)
        self._events[stream_name].append(event)

    def events_for(self, stream_name: str) -> list[WorkflowEvent]:
        return list(self._events.get(stream_name, []))

    def _validate_stream_name(self, stream_name: str) -> None:
        if stream_name.startswith("nd:"):
            raise InvalidStreamNamespaceError("Builder may not write to ND-owned stream")
        if not stream_name.startswith("builder:"):
            raise InvalidStreamNamespaceError("Builder workflow streams must use builder: namespace")
