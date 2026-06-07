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


class AuditEvent(BaseModel):
    """Immutable audit event for mutation tracking."""
    model_config = ConfigDict(extra="forbid", frozen=True)

    request_id: str
    actor_id: str
    action: str
    resource_type: str
    resource_id: str | None = None
    before_hash: str | None = None
    after_hash: str | None = None
    status: str
    error_code: str | None = None


def audit_event_from_mutation(
    *,
    request_id: str,
    actor_id: str,
    action: str,
    resource_type: str,
    resource_id: str | None = None,
    before_hash: str | None = None,
    after_hash: str | None = None,
    status: str = "success",
    error_code: str | None = None,
) -> AuditEvent:
    """Create an AuditEvent from a mutation action."""
    return AuditEvent(
        request_id=request_id,
        actor_id=actor_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        before_hash=before_hash,
        after_hash=after_hash,
        status=status,
        error_code=error_code,
    )
