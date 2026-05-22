from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class RuntimeEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    job_id: str
    stage: str
    level: str
    message: str
    progress_pct: float
