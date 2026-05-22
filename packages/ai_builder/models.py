from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class AiDraftResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    spec: dict[str, object]
    accepted: bool
    validation_errors: list[str]
    explanation: str
