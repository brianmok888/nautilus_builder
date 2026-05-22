from __future__ import annotations

import hashlib
import json

from packages.backtest_jobs.models import BacktestJob


class BacktestJobService:
    def __init__(self) -> None:
        self._jobs_by_key: dict[str, BacktestJob] = {}
        self._jobs_by_id: dict[str, BacktestJob] = {}

    def _make_key(self, payload: dict[str, str]) -> str:
        return json.dumps(payload, sort_keys=True, separators=(",", ":"))

    def _make_job_id(self, payload: dict[str, str]) -> str:
        digest = hashlib.sha256(self._make_key(payload).encode("utf-8")).hexdigest()[:12]
        return f"bt_{digest}"

    def create_job(self, payload: dict[str, str]) -> BacktestJob:
        key = self._make_key(payload)
        existing = self._jobs_by_key.get(key)
        if existing is not None:
            return existing

        job = BacktestJob(
            job_id=self._make_job_id(payload),
            stage="CREATED",
            strategy_spec_version=payload["strategy_spec_version"],
            adapter_id=payload["adapter_id"],
            instrument_id=payload["instrument_id"],
            compile_hash=payload["compile_hash"],
            validation_report_id=payload["validation_report_id"],
        )
        self._jobs_by_key[key] = job
        self._jobs_by_id[job.job_id] = job
        return job

    def get_job(self, job_id: str) -> BacktestJob:
        return self._jobs_by_id[job_id]

    def transition_job(self, job_id: str, stage: str) -> BacktestJob:
        job = self._jobs_by_id[job_id]
        updated = job.model_copy(update={"stage": stage})
        self._jobs_by_id[job_id] = updated
        self._jobs_by_key[self._make_key(self._payload_from_job(job))] = updated
        return updated

    def record_frontend_disconnect(self, job_id: str) -> BacktestJob:
        return self._jobs_by_id[job_id]

    def request_cancel(self, job_id: str) -> BacktestJob:
        job = self._jobs_by_id[job_id]
        updated = job.model_copy(update={"stage": "CANCEL_REQUESTED", "cancel_requested": True})
        self._jobs_by_id[job_id] = updated
        self._jobs_by_key[self._make_key(self._payload_from_job(job))] = updated
        return updated

    def _payload_from_job(self, job: BacktestJob) -> dict[str, str]:
        return {
            "strategy_spec_version": job.strategy_spec_version,
            "adapter_id": job.adapter_id,
            "instrument_id": job.instrument_id,
            "compile_hash": job.compile_hash,
            "validation_report_id": job.validation_report_id,
        }
