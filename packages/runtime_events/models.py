from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class RuntimeEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: str
    job_id: str
    actor_type: str
    actor_id: str
    stage: str
    level: str
    message: str
    timestamp: str
    metadata: dict[str, object]
    progress_pct: float
