from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime

from packages.auth import UserProjectContext, assert_same_project
from packages.backtest_jobs.models import BacktestJob


class BacktestJobService:
    def __init__(self) -> None:
        self._jobs_by_key: dict[str, BacktestJob] = {}
        self._jobs_by_id: dict[str, BacktestJob] = {}

    def _canonical_payload(self, payload: dict[str, object]) -> dict[str, str]:
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

    def _make_key(self, payload: dict[str, str]) -> str:
        return json.dumps(self._canonical_payload(payload), sort_keys=True, separators=(",", ":"))

    def _make_job_id(self, payload: dict[str, str]) -> str:
        digest = hashlib.sha256(self._make_key(payload).encode("utf-8")).hexdigest()[:12]
        return f"bt_{digest}"

    def _now(self) -> str:
        return datetime.now(UTC).isoformat().replace("+00:00", "Z")

    def _event_stream_id(self, job_id: str) -> str:
        return f"builder:runtime:{job_id}"

    def create_job(self, payload: dict[str, str]) -> BacktestJob:
        key = self._make_key(payload)
        existing = self._jobs_by_key.get(key)
        if existing is not None:
            return existing

        canonical = self._canonical_payload(payload)
        job_id = self._make_job_id(payload)
        now = self._now()
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
            event_stream_id=self._event_stream_id(job_id),
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
        self._jobs_by_key[key] = job
        self._jobs_by_id[job.job_id] = job
        return job

    def get_job(self, job_id: str, *, context: UserProjectContext | None = None) -> BacktestJob:
        job = self._jobs_by_id[job_id]
        if context is not None:
            assert_same_project(context, job.scoped_artifact)
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
        job = self.get_job(job_id, context=context)
        updates: dict[str, object] = {"stage": stage, "status": stage, "updated_at": self._now()}
        if worker_id is not None:
            updates["worker_id"] = worker_id
        if result_artifact_refs is not None:
            updates["result_artifact_refs"] = dict(result_artifact_refs)
        updated = job.model_copy(update=updates)
        self._jobs_by_id[job_id] = updated
        self._jobs_by_key[self._make_key(self._payload_from_job(updated))] = updated
        return updated

    def record_frontend_disconnect(self, job_id: str) -> BacktestJob:
        return self._jobs_by_id[job_id]

    def request_cancel(self, job_id: str, *, context: UserProjectContext | None = None) -> BacktestJob:
        job = self.get_job(job_id, context=context)
        updated = job.model_copy(
            update={
                "stage": "CANCEL_REQUESTED",
                "status": "CANCEL_REQUESTED",
                "updated_at": self._now(),
                "cancel_requested": True,
            }
        )
        self._jobs_by_id[job_id] = updated
        self._jobs_by_key[self._make_key(self._payload_from_job(updated))] = updated
        return updated

    def _payload_from_job(self, job: BacktestJob) -> dict[str, str]:
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
