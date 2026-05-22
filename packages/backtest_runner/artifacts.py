from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class BacktestResultArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    strategy_spec_version: str
    compile_hash: str
    worker_image: str
    summary_metrics: dict[str, float | int]
    artifact_refs: dict[str, str]
    logs: list[str]
