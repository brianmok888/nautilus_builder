"""Postgres-backed workflow result repository.

Reads/writes durable workflow results from the `workflow_results` table.
Drop-in replacement for the result-handling methods on InMemoryWorkflowRepository
when BUILDER_DATABASE_URL is configured.

This is pure persistence. No trading logic, no execution authority.
"""
from __future__ import annotations

import json
from typing import Any

from packages.workflow_spine.models import WorkflowResultRecord


class PostgresWorkflowResultRepository:
    """Postgres-backed workflow result repository."""

    def __init__(self, conn: Any, schema: str = "builder") -> None:
        self._conn = conn
        self._schema = schema

    def _table(self, name: str) -> str:
        return f"{self._schema}.{name}"

    def save_result(self, record: WorkflowResultRecord) -> None:
        """Persist a workflow result. INSERT ON CONFLICT DO UPDATE for idempotency.

        The full record (metrics, artifact_refs, strategy_version_id, etc.) is
        serialized into the payload JSONB column so the model round-trips exactly.
        """
        payload = record.model_dump(mode="json")
        payload_json = json.dumps(payload, sort_keys=True)
        self._conn.execute(
            f"""
            INSERT INTO {self._table("workflow_results")}
                (result_id, test_job_id, strategy_lineage_id, project_id, payload, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (result_id) DO UPDATE SET
                test_job_id = EXCLUDED.test_job_id,
                strategy_lineage_id = EXCLUDED.strategy_lineage_id,
                project_id = EXCLUDED.project_id,
                payload = EXCLUDED.payload
            """,
            (
                record.result_id,
                record.test_job_id,
                record.strategy_lineage_id,
                record.project_id,
                payload_json,
                record.created_at,
            ),
        )

    def result(self, result_id: str) -> WorkflowResultRecord | None:
        """Fetch a single workflow result by id, or None if not found."""
        row = self._conn.execute(
            f"""
            SELECT payload FROM {self._table("workflow_results")}
            WHERE result_id = %s
            """,
            (result_id,),
        ).fetchone()
        if not row:
            return None
        return self._row_to_record(row)

    def result_for_job(self, test_job_id: str) -> WorkflowResultRecord | None:
        """Fetch the workflow result for a given test job, or None if not found."""
        row = self._conn.execute(
            f"""
            SELECT payload FROM {self._table("workflow_results")}
            WHERE test_job_id = %s
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (test_job_id,),
        ).fetchone()
        if not row:
            return None
        return self._row_to_record(row)

    def list_results(
        self,
        *,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[WorkflowResultRecord]:
        """List workflow results newest-first, with optional limit/offset."""
        sql = f"""
            SELECT payload FROM {self._table("workflow_results")}
            ORDER BY created_at DESC
        """
        params: list[Any] = []
        if limit is not None or offset:
            sql += " LIMIT %s OFFSET %s"
            params.append(limit if limit is not None else 2_147_483_647)
            params.append(offset)
        rows = self._conn.execute(sql, params).fetchall()
        return [self._row_to_record(row) for row in rows]

    def results_for_lineage(self, strategy_lineage_id: str) -> list[WorkflowResultRecord]:
        """List all workflow results for a strategy lineage, newest-first."""
        rows = self._conn.execute(
            f"""
            SELECT payload FROM {self._table("workflow_results")}
            WHERE strategy_lineage_id = %s
            ORDER BY created_at DESC
            """,
            (strategy_lineage_id,),
        ).fetchall()
        return [self._row_to_record(row) for row in rows]

    @staticmethod
    def _row_to_record(row: tuple[Any, ...]) -> WorkflowResultRecord:
        """Convert a result row to a WorkflowResultRecord.

        psycopg3 returns JSONB columns as already-parsed Python dicts; fall back
        to json.loads for the text-serialized case to stay robust.
        """
        payload = row[0]
        if isinstance(payload, str):
            payload = json.loads(payload)
        return WorkflowResultRecord.model_validate(payload)
