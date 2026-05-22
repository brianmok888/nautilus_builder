from __future__ import annotations

from packages.workflow_spine.models import StrategyIdentity, StrategyVersionIdentity, TestJobRecord


class InMemoryWorkflowRepository:
    def __init__(self) -> None:
        self._strategies: dict[str, StrategyIdentity] = {}
        self._versions: dict[str, StrategyVersionIdentity] = {}
        self._jobs: dict[str, TestJobRecord] = {}

    def save_strategy(self, strategy: StrategyIdentity) -> None:
        self._strategies[strategy.strategy_id] = strategy

    def save_version(self, version: StrategyVersionIdentity) -> None:
        self._versions[version.strategy_version_id] = version

    def save_job(self, job: TestJobRecord) -> None:
        self._jobs[job.test_job_id] = job

    def strategy(self, strategy_id: str) -> StrategyIdentity | None:
        return self._strategies.get(strategy_id)

    def version(self, strategy_version_id: str) -> StrategyVersionIdentity | None:
        return self._versions.get(strategy_version_id)

    def job(self, test_job_id: str) -> TestJobRecord | None:
        return self._jobs.get(test_job_id)
