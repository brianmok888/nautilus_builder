"""Postgres-backed BacktestJobService.

Delegates business logic (key generation, hashing, job ID creation) to the
existing BacktestJobService patterns but persists to Postgres instead of
in-memory dictionaries.

This service is read-only with respect to trading authority: it does not
call submit_order, create TradeAction, or grant live execution.
"""
from __future__ import annotations


from packages.auth import UserProjectContext, assert_same_project
from packages.backtest_jobs.models import BacktestJob
from packages.postgres.backtest_job_repository import PostgresBacktestJobRepository


class PostgresBacktestJobService:
    """Postgres-backed backtest job service.

    Provides the same interface as BacktestJobService but with durable
    Postgres storage. Used when BUILDER_DATABASE_URL is configured.
    """

    def __init__(self, repo: PostgresBacktestJobRepository) -> None:
        self._repo = repo
        # Expose for evidence summary aggregation (same interface as BacktestJobService)
        self._jobs_by_id: dict[str, BacktestJob] = {}

    def _refresh_cache(self) -> None:
        """Refresh the in-memory cache from Postgres."""
        self._jobs_by_id = {job.job_id: job for job in self._repo.list_all()}

    def create_job(self, payload: dict[str, str]) -> BacktestJob:
        """Create a new backtest job, persisted to Postgres.

        If an equivalent job already exists in Postgres, return it (idempotent).
        """
        import hashlib
        import json
        from datetime import UTC, datetime

        # Normalize payload (same logic as in-memory service)
        canonical = self._canonical_payload(payload)
        key = json.dumps(canonical, sort_keys=True, separators=(",", ":"))

        # Check for existing job by scanning (idempotency)
        self._refresh_cache()
        for job in self._jobs_by_id.values():
            job_key = json.dumps(self._payload_from_job(job), sort_keys=True, separators=(",", ":"))
            if job_key == key:
                return job

        digest = hashlib.sha256(key.encode("utf-8")).hexdigest()[:12]
        job_id = f"bt_{digest}"
        now = datetime.now(UTC).isoformat().replace("+00:00", "Z")
        stream_id = f"builder:runtime:{job_id}"

        job = BacktestJob(
            job_id=job_id,
            status="CREATED",
            stage="CREATED",
            created_by=canonical["created_by"],
            created_at=now,
            updated_at=now,
            strategy_spec_version_id=canonical["strategy_spec_version_id"],
            adapter_profile_id=canonical["adapter_profile_id"],
            instrument_id=canonical["instrument_id"],
            data_range=canonical["data_range"],
            worker_id="unassigned",
            result_artifact_refs={},
            event_stream_id=stream_id,
            user_id=canonical["user_id"],
            project_id=canonical["project_id"],
            dataset_id=canonical["dataset_id"],
            catalog_path=canonical["catalog_path"] or None,
            data_type=canonical["data_type"],
            timeframe=canonical["timeframe"],
            market_type=canonical["market_type"],
            compile_hash=canonical["compile_hash"],
            validation_report_id=canonical["validation_report_id"],
            compile_artifact_id=canonical["compile_artifact_id"] or None,
        )
        self._repo.save(job)
        self._jobs_by_id[job.job_id] = job
        return job

    def get_job(self, job_id: str, *, context: UserProjectContext | None = None) -> BacktestJob:
        """Get a job by ID. Raises KeyError if not found."""
        job = self._repo.get(job_id)
        if job is None:
            raise KeyError(f"job not found: {job_id}")
        if context is not None:
            assert_same_project(context, job.scoped_artifact)
        self._jobs_by_id[job.job_id] = job
        return job

    def transition_job(
        self,
        job_id: str,
        stage: str,
        *,
        worker_id: str | None = None,
        result_artifact_refs: dict[str, str] | None = None,
        context: UserProjectContext | None = None,
    ) -> BacktestJob:
        """Transition a job to a new stage."""
        # Verify job exists and user has access
        self.get_job(job_id, context=context)

        job = self._repo.update_status(
            job_id,
            stage,
            worker_id=worker_id,
            result_artifact_refs=result_artifact_refs,
        )
        if job is not None:
            self._jobs_by_id[job.job_id] = job
        return job if job is not None else self._jobs_by_id[job_id]

    def record_frontend_disconnect(self, job_id: str) -> BacktestJob:
        """Record that the frontend disconnected. No-op for Postgres."""
        return self.get_job(job_id)

    def request_cancel(self, job_id: str, *, context: UserProjectContext | None = None) -> BacktestJob:
        """Request cancellation of a job."""
        self.get_job(job_id, context=context)
        job = self._repo.request_cancel(job_id)
        if job is not None:
            self._jobs_by_id[job.job_id] = job
        return job if job is not None else self._jobs_by_id[job_id]

    @staticmethod
    def _canonical_payload(payload: dict[str, object]) -> dict[str, str]:
        return {
            "strategy_spec_version_id": str(
                payload.get("strategy_spec_version_id")
                or payload.get("strategy_spec_version")
                or payload.get("strategy_version_id")
                or ""
            ),
            "adapter_profile_id": str(payload.get("adapter_profile_id") or payload.get("adapter_id") or ""),
            "instrument_id": str(payload.get("instrument_id") or ""),
            "compile_hash": str(payload.get("compile_hash") or payload.get("compile_artifact_id") or ""),
            "validation_report_id": str(payload.get("validation_report_id") or ""),
            "compile_artifact_id": str(payload.get("compile_artifact_id") or ""),
            "created_by": str(payload.get("created_by") or "builder_api"),
            "data_range": str(payload.get("data_range") or "unspecified"),
            "user_id": str(payload.get("user_id") or "system"),
            "project_id": str(payload.get("project_id") or "default"),
            "dataset_id": str(payload.get("dataset_id") or "unspecified"),
            "catalog_path": str(payload.get("catalog_path") or ""),
            "data_type": str(payload.get("data_type") or "unspecified"),
            "timeframe": str(payload.get("timeframe") or "unspecified"),
            "market_type": str(payload.get("market_type") or "unspecified"),
        }

    @staticmethod
    def _payload_from_job(job: BacktestJob) -> dict[str, str]:
        return {
            "strategy_spec_version_id": job.strategy_spec_version_id,
            "adapter_profile_id": job.adapter_profile_id,
            "instrument_id": job.instrument_id,
            "compile_hash": job.compile_hash,
            "validation_report_id": job.validation_report_id,
            "compile_artifact_id": job.compile_artifact_id or "",
            "created_by": job.created_by,
            "data_range": job.data_range,
            "user_id": job.user_id,
            "project_id": job.project_id,
            "dataset_id": job.dataset_id,
            "catalog_path": job.catalog_path or "",
            "data_type": job.data_type,
            "timeframe": job.timeframe,
            "market_type": job.market_type,
        }
