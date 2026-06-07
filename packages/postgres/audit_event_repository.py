"""Postgres-backed audit event repository for durable audit trail.

Writes audit events from the API middleware to the `audit_events` table.
Fails closed: critical promotion/deployment mutations must have audit evidence.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


class PostgresAuditEventRepository:
    """Repository for writing audit events to Postgres.

    Uses the connection pool from packages.postgres.connection.
    """

    def __init__(self, pool: Any = None) -> None:
        self._pool = pool

    async def write_audit_event(
        self,
        *,
        request_id: str,
        actor_id: str | None = None,
        project_id: str | None = None,
        action: str,
        resource_type: str,
        resource_id: str | None = None,
        before_hash: str | None = None,
        after_hash: str | None = None,
        status: str = "success",
        error_code: str | None = None,
    ) -> str | None:
        """Write an audit event to the audit_events table.

        Returns the event ID if written, None if pool unavailable.
        """
        if self._pool is None:
            logger.debug("audit_event_skip_no_pool request_id=%s", request_id)
            return None

        event_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()

        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO builder.audit_events
                    (id, request_id, actor_id, project_id, action,
                     resource_type, resource_id, before_hash, after_hash,
                     status, error_code, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                """,
                event_id,
                request_id,
                actor_id,
                project_id,
                action,
                resource_type,
                resource_id,
                before_hash,
                after_hash,
                status,
                error_code,
                created_at,
            )

        logger.info(
            "audit_event_written id=%s request_id=%s action=%s resource=%s/%s",
            event_id,
            request_id,
            action,
            resource_type,
            resource_id,
        )
        return event_id

    async def query_audit_events(
        self,
        *,
        actor_id: str | None = None,
        project_id: str | None = None,
        resource_type: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Query audit events with optional filters."""
        if self._pool is None:
            return []

        conditions: list[str] = []
        params: list[Any] = []
        idx = 1

        if actor_id is not None:
            conditions.append(f"actor_id = ${idx}")
            params.append(actor_id)
            idx += 1

        if project_id is not None:
            conditions.append(f"project_id = ${idx}")
            params.append(project_id)
            idx += 1

        if resource_type is not None:
            conditions.append(f"resource_type = ${idx}")
            params.append(resource_type)
            idx += 1

        where = f" WHERE {' AND '.join(conditions)}" if conditions else ""
        params.append(limit)

        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                f"""
                SELECT id, request_id, actor_id, project_id, action,
                       resource_type, resource_id, before_hash, after_hash,
                       status, error_code, created_at
                FROM builder.audit_events
                {where}
                ORDER BY created_at DESC
                LIMIT ${idx}
                """,
                *params,
            )

        return [dict(row) for row in rows]


def make_audit_writer_from_pool(pool: Any) -> "AuditWriter":
    """Create an audit writer function backed by a Postgres pool.

    Returns a callable that matches the AuditMiddleware writer signature.
    """
    repo = PostgresAuditEventRepository(pool=pool)

    def audit_writer(event: dict) -> None:
        """Sync wrapper that schedules async write (fire-and-forget for middleware)."""
        import asyncio

        try:
            loop = asyncio.get_running_loop()
            loop.create_task(
                repo.write_audit_event(
                    request_id=event.get("request_id", ""),
                    actor_id=event.get("actor_id"),
                    project_id=event.get("project_id"),
                    action=f"{event.get('method', '')} {event.get('route', '')}".strip(),
                    resource_type=event.get("resource_type", "unknown"),
                    resource_id=event.get("resource_id"),
                    status="success" if 200 <= event.get("status_code", 0) < 400 else "failed",
                )
            )
        except RuntimeError:
            logger.warning("audit_event_no_event_loop request_id=%s", event.get("request_id"))

    return audit_writer
