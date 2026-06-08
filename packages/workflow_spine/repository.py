from __future__ import annotations

from packages.auth import ProjectScopeError, UserProjectContext
from packages.workflow_spine.models import (
    AiSuggestionRecord,
    StrategyIdentity,
    StrategyVersionIdentity,
    WorkflowJobRecord,
    WorkflowResultRecord,
)


class InMemoryWorkflowRepository:
    def __init__(self) -> None:
        self._strategies: dict[str, StrategyIdentity] = {}
        self._versions: dict[str, StrategyVersionIdentity] = {}
        self._jobs: dict[str, WorkflowJobRecord] = {}
        self._results: dict[str, WorkflowResultRecord] = {}
        self._suggestions: dict[str, AiSuggestionRecord] = {}

    def save_strategy(self, strategy: StrategyIdentity) -> None:
        self._strategies[strategy.strategy_id] = strategy

    def save_version(self, version: StrategyVersionIdentity) -> None:
        self._versions[version.strategy_version_id] = version

    def save_job(self, job: WorkflowJobRecord) -> None:
        self._jobs[job.test_job_id] = job

    def strategy(self, strategy_id: str) -> StrategyIdentity | None:
        return self._strategies.get(strategy_id)

    def version(self, strategy_version_id: str) -> StrategyVersionIdentity | None:
        return self._versions.get(strategy_version_id)

    def job(self, test_job_id: str) -> WorkflowJobRecord | None:
        return self._jobs.get(test_job_id)

    def save_result(self, result: WorkflowResultRecord) -> None:
        self._results[result.result_id] = result

    def result(
        self,
        result_id: str,
        *,
        context: UserProjectContext | None = None,
    ) -> WorkflowResultRecord | None:
        result = self._results.get(result_id)
        if result is not None and context is not None and result.project_id != context.project_id:
            raise ProjectScopeError(f"result {result_id} is outside project scope")
        return result

    def result_for_job(self, test_job_id: str) -> WorkflowResultRecord | None:
        for result in self._results.values():
            if result.test_job_id == test_job_id:
                return result
        return None

    def list_results(
        self,
        *,
        limit: int | None = None,
        offset: int = 0,
        context: UserProjectContext | None = None,
    ) -> list[WorkflowResultRecord]:
        scoped_results = [
            result
            for result in self._results.values()
            if context is None or result.project_id == context.project_id
        ]
        all_results = sorted(scoped_results, key=lambda r: r.created_at)
        start = min(offset, len(all_results))
        sliced = all_results[start:]
        if limit is not None:
            sliced = sliced[:limit]
        return sliced

    def save_ai_suggestion(self, suggestion: AiSuggestionRecord) -> None:
        self._suggestions[suggestion.suggestion_id] = suggestion

    def suggestions_for_lineage(
        self,
        strategy_lineage_id: str,
        *,
        context: UserProjectContext | None = None,
    ) -> list[AiSuggestionRecord]:
        suggestions = [
            suggestion
            for suggestion in self._suggestions.values()
            if suggestion.strategy_lineage_id == strategy_lineage_id
        ]
        return self._scope_suggestions(suggestions, context=context, identifier=strategy_lineage_id)

    def suggestions_for_result(
        self,
        result_id: str,
        *,
        context: UserProjectContext | None = None,
    ) -> list[AiSuggestionRecord]:
        suggestions = [suggestion for suggestion in self._suggestions.values() if suggestion.result_id == result_id]
        return self._scope_suggestions(suggestions, context=context, identifier=result_id)

    def suggestions_for_ai_thread(
        self,
        ai_thread_id: str,
        *,
        context: UserProjectContext | None = None,
    ) -> list[AiSuggestionRecord]:
        suggestions = [suggestion for suggestion in self._suggestions.values() if suggestion.ai_thread_id == ai_thread_id]
        return self._scope_suggestions(suggestions, context=context, identifier=ai_thread_id)

    @staticmethod
    def _scope_suggestions(
        suggestions: list[AiSuggestionRecord],
        *,
        context: UserProjectContext | None,
        identifier: str,
    ) -> list[AiSuggestionRecord]:
        if context is None:
            return suggestions
        scoped = [suggestion for suggestion in suggestions if suggestion.project_id == context.project_id]
        if suggestions and not scoped:
            raise ProjectScopeError(f"workflow suggestions for {identifier} are outside project scope")
        return scoped
