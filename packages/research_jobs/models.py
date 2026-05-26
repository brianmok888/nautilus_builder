from __future__ import annotations

import hashlib
import json
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ResearchJobType(str, Enum):
    PARAMETER_SEARCH = "parameter_search"


class ResearchJobStatus(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELED = "CANCELED"


class ResearchWindow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    date_range: str = Field(min_length=1)


class ResearchJob(BaseModel):
    model_config = ConfigDict(extra="forbid")

    research_job_id: str | None = None
    strategy_lineage_id: str = Field(min_length=1)
    strategy_version_id: str = Field(min_length=1)
    dataset_id: str = Field(min_length=1)
    job_type: ResearchJobType = ResearchJobType.PARAMETER_SEARCH
    parameter_grid: dict[str, list[int | float | str | bool]] = Field(default_factory=dict)
    train_windows: list[ResearchWindow] = Field(default_factory=list)
    holdout_windows: list[ResearchWindow] = Field(default_factory=list)
    max_trials: int = Field(default=16, ge=1)
    created_by: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    status: ResearchJobStatus = ResearchJobStatus.QUEUED
    execution_mode: Literal["offline_research"] = "offline_research"
    auto_promote: Literal[False] = False
    manual_promotion_required: Literal[True] = True
    may_submit_order: Literal[False] = False
    live_trading_enabled: Literal[False] = False
    execution_authority: Literal[False] = False

    @model_validator(mode="before")
    @classmethod
    def populate_job_id(cls, data: object) -> object:
        if isinstance(data, dict) and not data.get("research_job_id"):
            candidate = dict(data)
            material = {
                "strategy_lineage_id": candidate.get("strategy_lineage_id"),
                "strategy_version_id": candidate.get("strategy_version_id"),
                "dataset_id": candidate.get("dataset_id"),
                "job_type": candidate.get("job_type", ResearchJobType.PARAMETER_SEARCH.value),
                "parameter_grid": candidate.get("parameter_grid", {}),
                "train_windows": candidate.get("train_windows", []),
                "holdout_windows": candidate.get("holdout_windows", []),
                "max_trials": candidate.get("max_trials", 16),
                "created_by": candidate.get("created_by"),
                "project_id": candidate.get("project_id"),
            }
            digest = hashlib.sha256(json.dumps(material, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest()
            candidate["research_job_id"] = f"research_job_{digest[:16]}"
            return candidate
        return data

    @model_validator(mode="after")
    def validate_research_policy(self) -> "ResearchJob":
        if not self.parameter_grid:
            raise ValueError("parameter_grid must not be empty")
        if not self.train_windows:
            raise ValueError("train_windows must not be empty")
        return self
