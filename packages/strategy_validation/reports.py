from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class ValidationReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    is_valid: bool
    errors: list[str]
    warnings: list[str] = []
