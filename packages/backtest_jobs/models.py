from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from packages.auth import ScopedArtifactRef


class BacktestJob(BaseModel):
    model_config = ConfigDict(extra="forbid")

    job_id: str
    status: str
    stage: str
    created_by: str
    created_at: str
    updated_at: str
    strategy_spec_version_id: str
    adapter_profile_id: str
    instrument_id: str
    data_range: str
    worker_id: str
    result_artifact_refs: dict[str, str]
    event_stream_id: str
    user_id: str = "system"
    project_id: str = "default"
    dataset_id: str = "unspecified"
    catalog_path: str | None = None
    data_type: str = "unspecified"
    timeframe: str = "unspecified"
    market_type: str = "unspecified"
    compile_hash: str
    validation_report_id: str
    cancel_requested: bool = False

    @property
    def strategy_spec_version(self) -> str:
        return self.strategy_spec_version_id

    @property
    def adapter_id(self) -> str:
        return self.adapter_profile_id

    @property
    def scoped_artifact(self) -> ScopedArtifactRef:
        return ScopedArtifactRef(
            artifact_type="BacktestJob",
            artifact_id=self.job_id,
            user_id=self.user_id,
            project_id=self.project_id,
        )
