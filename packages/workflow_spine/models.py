from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field


class StrategyIdentity(BaseModel):
    model_config = ConfigDict(extra="forbid")

    strategy_id: str = Field(min_length=1)
    strategy_lineage_id: str = Field(min_length=1)
    display_name: str = Field(min_length=1)
    source_ref: str | None = None

    @property
    def continuity_key(self) -> str:
        return self.strategy_lineage_id


class StrategyVersionIdentity(BaseModel):
    model_config = ConfigDict(extra="forbid")

    strategy_id: str = Field(min_length=1)
    strategy_lineage_id: str = Field(min_length=1)
    strategy_version_id: str = Field(min_length=1)
    parent_version_id: str | None = None
    ai_thread_id: str | None = None
    improvement_cycle_id: str | None = None
    revision_reason: str | None = None

    @property
    def continuity_key(self) -> str:
        return self.strategy_lineage_id


class WorkflowEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    strategy_id: str | None = None
    strategy_lineage_id: str | None = None
    strategy_version_id: str | None = None
    test_job_id: str | None = None
    result_id: str | None = None
    ai_thread_id: str | None = None
    improvement_cycle_id: str | None = None

    def to_stream_payload(self) -> dict[str, str]:
        return self.model_dump(mode="json", exclude_none=True)


class StrategyTestParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    test_type: str = Field(min_length=1)
    instrument: str = Field(min_length=1)
    data_source: str = Field(min_length=1)
    timeframe: str = Field(min_length=1)
    start: str = Field(min_length=1)
    end: str = Field(min_length=1)


class WorkflowJobRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    test_job_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    strategy_version_id: str = Field(min_length=1)
    strategy_lineage_id: str = Field(min_length=1)
    test_type: str = Field(min_length=1)
    params: StrategyTestParams


class StrategyTestWorkflowOutcome(BaseModel):
    model_config = ConfigDict(extra="forbid")

    strategy: StrategyIdentity
    version: StrategyVersionIdentity
    job: WorkflowJobRecord


class WorkflowResultRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    result_id: str = Field(min_length=1)
    test_job_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    strategy_lineage_id: str = Field(min_length=1)
    strategy_version_id: str = Field(min_length=1)
    metrics: dict[str, float]
    artifact_refs: dict[str, str]
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class AiSuggestionRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    suggestion_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    strategy_lineage_id: str = Field(min_length=1)
    strategy_version_id: str = Field(min_length=1)
    result_id: str = Field(min_length=1)
    ai_thread_id: str = Field(min_length=1)
    improvement_cycle_id: str = Field(min_length=1)
    suggestion_type: str = Field(min_length=1)
    message: str = Field(min_length=1)
