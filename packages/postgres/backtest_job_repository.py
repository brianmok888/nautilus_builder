"""Postgres-backed backtest job repository.

Drop-in replacement for the in-memory storage in BacktestJobService.
Reads and writes BacktestJob records to the `backtest_jobs` table.
"""
from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from packages.auth import UserProjectContext
from packages.backtest_jobs.models import BacktestJob
from packages.postgres.identifiers import postgres_table, safe_postgres_identifier


def _now_iso() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


_COLUMNS = (
    "job_id, strategy_id, strategy_spec_version_id, adapter_profile_id, "
    "instrument_id, data_range, compile_hash, compile_artifact_id, "
    "validation_report_id, status, stage, lifecycle_status, worker_id, "
    "result_artifact_refs, event_stream_id, created_by, user_id, project_id, "
    "dataset_id, catalog_path, data_type, timeframe, market_type, "
    "cancel_requested, created_at, updated_at"
)


class PostgresBacktestJobRepository:
    """Postgres-backed backtest job repository.

    Uses synchronous psycopg3 connections (same pattern as PostgresStrategyRepository).
    """

    def __init__(self, conn: Any, schema: str = "builder") -> None:
        self._conn = conn
        self._schema = safe_postgres_identifier(schema)

    def _table(self) -> str:
        return postgres_table(self._schema, "backtest_jobs")

    @staticmethod
    def _row_to_job(row: tuple) -> BacktestJob:
        """Convert a database row tuple to a BacktestJob model."""
        (
            job_id,
            _strategy_id,
            strategy_spec_version_id,
            adapter_profile_id,
            instrument_id,
            data_range,
            compile_hash,
            compile_artifact_id,
            validation_report_id,
            status,
            stage,
            _lifecycle_status,
            worker_id,
            result_artifact_refs_raw,
            event_stream_id,
            created_by,
            user_id,
            project_id,
            dataset_id,
            catalog_path,
            data_type,
            timeframe,
            market_type,
            cancel_requested,
            created_at,
            updated_at,
        ) = row

        refs = result_artifact_refs_raw
        if isinstance(refs, str):
            refs = json.loads(refs)
        elif refs is None:
            refs = {}

        def _ts(v: Any) -> str:
            if v is None:
                return ""
            if isinstance(v, str):
                return v
            return v.isoformat().replace("+00:00", "Z")

        return BacktestJob(
            job_id=job_id,
            status=status,
            stage=stage,
            created_by=created_by,
            created_at=_ts(created_at),
            updated_at=_ts(updated_at),
            strategy_spec_version_id=strategy_spec_version_id,
            adapter_profile_id=adapter_profile_id,
            instrument_id=instrument_id,
            data_range=data_range,
            worker_id=worker_id,
            result_artifact_refs=refs,
            event_stream_id=event_stream_id,
            user_id=user_id,
            project_id=project_id,
            dataset_id=dataset_id,
            catalog_path=catalog_path,
            data_type=data_type,
            timeframe=timeframe,
            market_type=market_type,
            compile_hash=compile_hash,
            validation_report_id=validation_report_id,
            compile_artifact_id=compile_artifact_id,
            cancel_requested=bool(cancel_requested),
        )

    def save(self, job: BacktestJob) -> None:
        """Insert or update a BacktestJob. Idempotent via ON CONFLICT."""
        refs_json = json.dumps(job.result_artifact_refs)
        self._conn.execute(
            f"""
            INSERT INTO {self._table()} (
                job_id, strategy_id, strategy_spec_version_id, adapter_profile_id,
                instrument_id, data_range, compile_hash, compile_artifact_id,
                validation_report_id, status, stage, lifecycle_status, worker_id,
                result_artifact_refs, event_stream_id, created_by, user_id, project_id,
                dataset_id, catalog_path, data_type, timeframe, market_type,
                cancel_requested, created_at, updated_at
            ) VALUES (
                %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s
            )
            ON CONFLICT (job_id) DO UPDATE SET
                status = EXCLUDED.status,
                stage = EXCLUDED.stage,
                lifecycle_status = EXCLUDED.lifecycle_status,
                worker_id = EXCLUDED.worker_id,
                result_artifact_refs = EXCLUDED.result_artifact_refs,
                cancel_requested = EXCLUDED.cancel_requested,
                updated_at = EXCLUDED.updated_at
            """,
            (
                job.job_id,
                job.strategy_spec_version_id,
                job.strategy_spec_version_id,
                job.adapter_profile_id,
                job.instrument_id,
                job.data_range,
                job.compile_hash,
                job.compile_artifact_id,
                job.validation_report_id,
                job.status,
                job.stage,
                job.stage,
                job.worker_id,
                refs_json,
                job.event_stream_id,
                job.created_by,
                job.user_id,
                job.project_id,
                job.dataset_id,
                job.catalog_path,
                job.data_type,
                job.timeframe,
                job.market_type,
                job.cancel_requested,
                job.created_at,
                job.updated_at,
            ),
        )

    def get(self, job_id: str) -> BacktestJob | None:
        """Return a BacktestJob by job_id, or None if not found."""
        row = self._conn.execute(
            f"SELECT {_COLUMNS} FROM {self._table()} WHERE job_id = %s",
            (job_id,),
        ).fetchone()
        if row is None:
            return None
        return self._row_to_job(row)

    def list_by_strategy_version(
        self,
        strategy_spec_version_id: str,
        *,
        context: UserProjectContext | None = None,
    ) -> list[BacktestJob]:
        """Return all jobs for a given strategy version, ordered by creation time."""
        params: list[Any] = [strategy_spec_version_id]
        scope_clause = ""
        if context is not None:
            scope_clause = " AND user_id = %s AND project_id = %s"
            params.extend([context.user_id, context.project_id])
        rows = self._conn.execute(
            f"SELECT {_COLUMNS} FROM {self._table()} "
            f"WHERE strategy_spec_version_id = %s{scope_clause} ORDER BY created_at",
            tuple(params),
        ).fetchall()
        return [self._row_to_job(r) for r in rows]

    def list_all(self) -> list[BacktestJob]:
        """Return all backtest jobs ordered by creation time."""
        rows = self._conn.execute(
            f"SELECT {_COLUMNS} FROM {self._table()} ORDER BY created_at",
        ).fetchall()
        return [self._row_to_job(r) for r in rows]

    def update_status(
        self,
        job_id: str,
        stage: str,
        *,
        worker_id: str | None = None,
        result_artifact_refs: dict[str, str] | None = None,
    ) -> BacktestJob | None:
        """Update a job's stage/status and optional fields. Returns updated job or None."""
        sets = ["stage = %s", "status = %s", "lifecycle_status = %s", "updated_at = %s"]
        params: list[Any] = [stage, stage, stage, _now_iso()]

        if worker_id is not None:
            sets.append("worker_id = %s")
            params.append(worker_id)

        if result_artifact_refs is not None:
            sets.append("result_artifact_refs = %s")
            params.append(json.dumps(result_artifact_refs))

        params.append(job_id)

        row = self._conn.execute(
            f"UPDATE {self._table()} SET {', '.join(sets)} "
            f"WHERE job_id = %s RETURNING {_COLUMNS}",
            tuple(params),
        ).fetchone()
        if row is None:
            return None
        return self._row_to_job(row)

    def request_cancel(self, job_id: str) -> BacktestJob | None:
        """Mark a job as cancel-requested. Returns updated job or None."""
        now = _now_iso()
        row = self._conn.execute(
            f"UPDATE {self._table()} SET "
            f"stage = %s, status = %s, lifecycle_status = %s, "
            f"cancel_requested = true, updated_at = %s "
            f"WHERE job_id = %s RETURNING {_COLUMNS}",
            ("CANCEL_REQUESTED", "CANCEL_REQUESTED", "CANCEL_REQUESTED", now, job_id),
        ).fetchone()
        if row is None:
            return None
        return self._row_to_job(row)
