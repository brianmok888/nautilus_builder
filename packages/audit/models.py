"""Audit event model — structured lineage for all mutations."""
from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field


class AuditEvent(BaseModel):
    """Structured audit event for Builder mutations."""
    model_config = ConfigDict(extra="forbid")

    audit_event_id: str = Field(min_length=1)
    event_type: str = Field(min_length=1)
    actor_id: str = ""
    tenant_id: str = ""
    request_id: str = ""
    entity_type: str = ""
    entity_id: str = ""
    before_hash: str | None = None
    after_hash: str | None = None
    created_at_utc: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict = Field(default_factory=dict)


# Required audit event types
REQUIRED_AUDIT_EVENTS = {
    "strategy.created",
    "strategy.updated",
    "strategy.validated",
    "strategy.compiled",
    "backtest.started",
    "backtest.completed",
    "backtest.failed",
    "evidence.created",
    "evidence.verified",
    "evidence.failed",
    "promotion.requested",
    "promotion.blocked",
    "promotion.approved",
    "readiness.checked",
    "config.changed",
}
