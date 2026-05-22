from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from packages.workflow_spine.event_stream import InMemoryWorkflowStream
from packages.workflow_spine.models import WorkflowEvent


class NdAdvisoryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    stream_name: str = Field(min_length=1)
    payload: dict[str, str]


class NdAdvisoryMapper:
    def __init__(self, *, output_stream: str = "builder:nd:advisory") -> None:
        self._output_stream = output_stream

    def to_advisory_request(
        self,
        event: WorkflowEvent,
        *,
        source_ref: str | None = None,
        display_name: str | None = None,
    ) -> NdAdvisoryRequest:
        # Reuse the same namespace policy as the stream publisher without publishing.
        InMemoryWorkflowStream()._validate_stream_name(self._output_stream)
        payload = event.to_stream_payload()
        if source_ref is not None:
            payload["source_ref"] = source_ref
        if display_name is not None:
            payload["display_name"] = display_name
        return NdAdvisoryRequest(stream_name=self._output_stream, payload=payload)
