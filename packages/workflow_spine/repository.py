from __future__ import annotations

from packages.workflow_spine.models import (
    AiSuggestionRecord,
    StrategyIdentity,
    StrategyVersionIdentity,
    TestJobRecord,
    TestResultRecord,
)


class InMemoryWorkflowRepository:
    def __init__(self) -> None:
        self._strategies: dict[str, StrategyIdentity] = {}
        self._versions: dict[str, StrategyVersionIdentity] = {}
        self._jobs: dict[str, TestJobRecord] = {}
        self._results: dict[str, TestResultRecord] = {}
        self._suggestions: dict[str, AiSuggestionRecord] = {}

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

    def save_result(self, result: TestResultRecord) -> None:
        self._results[result.result_id] = result

    def result(self, result_id: str) -> TestResultRecord | None:
        return self._results.get(result_id)

    def result_for_job(self, test_job_id: str) -> TestResultRecord | None:
        for result in self._results.values():
            if result.test_job_id == test_job_id:
                return result
        return None

    def save_ai_suggestion(self, suggestion: AiSuggestionRecord) -> None:
        self._suggestions[suggestion.suggestion_id] = suggestion

    def suggestions_for_lineage(self, strategy_lineage_id: str) -> list[AiSuggestionRecord]:
        return [
            suggestion
            for suggestion in self._suggestions.values()
            if suggestion.strategy_lineage_id == strategy_lineage_id
        ]

    def suggestions_for_result(self, result_id: str) -> list[AiSuggestionRecord]:
        return [suggestion for suggestion in self._suggestions.values() if suggestion.result_id == result_id]

    def suggestions_for_ai_thread(self, ai_thread_id: str) -> list[AiSuggestionRecord]:
        return [suggestion for suggestion in self._suggestions.values() if suggestion.ai_thread_id == ai_thread_id]
