"""Readiness models — capability readiness matrix with evidence requirements."""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class ReadinessStatus(str, Enum):
    READY = "ready"
    PARTIAL = "partial"
    BLOCKED = "blocked"
    OUT_OF_SCOPE = "out_of_scope"


class ReadinessEntry(BaseModel):
    """Single readiness capability entry."""
    model_config = ConfigDict(extra="forbid")

    capability: str
    status: ReadinessStatus
    required_evidence_types: list[str] = Field(default_factory=list)
    blocking_reasons: list[str] = Field(default_factory=list)
    last_verified_at: str | None = None
    verified_by_command: str | None = None


class ReadinessMatrix(BaseModel):
    """Complete readiness matrix for all Builder capabilities."""
    model_config = ConfigDict(extra="forbid")

    builder_version: str
    checked_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    entries: list[ReadinessEntry]

    @property
    def live_execution_ready(self) -> bool:
        """Live execution must never be ready in Builder."""
        for entry in self.entries:
            if entry.capability == "live_execution":
                return entry.status != ReadinessStatus.OUT_OF_SCOPE
        return False
