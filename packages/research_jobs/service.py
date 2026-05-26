from __future__ import annotations

from .models import ResearchJob


class ResearchJobService:
    """Offline-only optimizer/research job registry for Builder backtest analysis."""

    def __init__(self) -> None:
        self._jobs: dict[str, ResearchJob] = {}

    def create_job(self, payload: dict[str, object]) -> ResearchJob:
        if payload.get("auto_promote") is True:
            raise ValueError("research jobs require manual promotion review")
        if payload.get("execution_mode", "offline_research") != "offline_research":
            raise ValueError("research jobs must use offline_research execution_mode")
        job = ResearchJob.model_validate(payload)
        self._jobs[job.research_job_id] = job
        return job

    def get_job(self, research_job_id: str) -> ResearchJob:
        return self._jobs[research_job_id]

    def list_jobs(self, *, project_id: str | None = None) -> list[ResearchJob]:
        jobs = list(self._jobs.values())
        if project_id is not None:
            jobs = [job for job in jobs if job.project_id == project_id]
        return jobs
