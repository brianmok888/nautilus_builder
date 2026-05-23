from __future__ import annotations

from itertools import count

from packages.workflow_spine.event_stream import InMemoryWorkflowStream
from packages.workflow_spine.models import (
    AiSuggestionRecord,
    StrategyIdentity,
    StrategyTestParams,
    StrategyTestWorkflowOutcome,
    StrategyVersionIdentity,
    TestJobRecord,
    TestResultRecord,
    WorkflowEvent,
)
from packages.workflow_spine.repository import InMemoryWorkflowRepository


class StrategyTestWorkflowService:
    def __init__(self, *, repository: InMemoryWorkflowRepository, stream: InMemoryWorkflowStream) -> None:
        self._repository = repository
        self._stream = stream
        self._counter = count(1)

    def create_version_and_enqueue_test(
        self,
        *,
        project_id: str,
        display_name: str,
        test_type: str,
        instrument: str,
        data_source: str,
        timeframe: str,
        start: str,
        end: str,
        ai_thread_id: str | None = None,
        improvement_cycle_id: str | None = None,
    ) -> StrategyTestWorkflowOutcome:
        seq = next(self._counter)
        strategy = StrategyIdentity(
            strategy_id=f"strat_{seq:03d}",
            strategy_lineage_id=f"lineage_{seq:03d}",
            display_name=display_name,
        )
        version = StrategyVersionIdentity(
            strategy_id=strategy.strategy_id,
            strategy_lineage_id=strategy.strategy_lineage_id,
            strategy_version_id=f"sv_{seq:03d}",
            ai_thread_id=ai_thread_id,
            improvement_cycle_id=improvement_cycle_id,
            revision_reason="initial workflow version",
        )
        params = StrategyTestParams(
            test_type=test_type,
            instrument=instrument,
            data_source=data_source,
            timeframe=timeframe,
            start=start,
            end=end,
        )
        job = TestJobRecord(
            test_job_id=f"job_{seq:03d}",
            project_id=project_id,
            strategy_version_id=version.strategy_version_id,
            strategy_lineage_id=strategy.strategy_lineage_id,
            test_type=test_type,
            params=params,
        )

        self._repository.save_strategy(strategy)
        self._repository.save_version(version)
        self._repository.save_job(job)

        self._stream.publish(
            "builder:workflow:events",
            WorkflowEvent(
                event="strategy.versioned",
                project_id=project_id,
                strategy_id=strategy.strategy_id,
                strategy_lineage_id=strategy.strategy_lineage_id,
                strategy_version_id=version.strategy_version_id,
                ai_thread_id=ai_thread_id,
                improvement_cycle_id=improvement_cycle_id,
            ),
        )
        self._stream.publish(
            "builder:test:jobs",
            WorkflowEvent(
                event="test.enqueued",
                project_id=project_id,
                strategy_id=strategy.strategy_id,
                strategy_lineage_id=strategy.strategy_lineage_id,
                strategy_version_id=version.strategy_version_id,
                test_job_id=job.test_job_id,
                ai_thread_id=ai_thread_id,
                improvement_cycle_id=improvement_cycle_id,
            ),
        )
        return StrategyTestWorkflowOutcome(strategy=strategy, version=version, job=job)

    def record_result_completed(
        self,
        *,
        test_job_id: str,
        result_id: str,
        metrics: dict[str, float],
        artifact_refs: dict[str, str],
    ) -> TestResultRecord:
        job = self._repository.job(test_job_id)
        if job is None:
            raise ValueError(f"unknown test job: {test_job_id}")
        result = TestResultRecord(
            result_id=result_id,
            test_job_id=test_job_id,
            project_id=job.project_id,
            strategy_lineage_id=job.strategy_lineage_id,
            strategy_version_id=job.strategy_version_id,
            metrics=metrics,
            artifact_refs=artifact_refs,
        )
        self._repository.save_result(result)
        self._stream.publish(
            "builder:workflow:events",
            WorkflowEvent(
                event="result.completed",
                project_id=result.project_id,
                strategy_lineage_id=result.strategy_lineage_id,
                strategy_version_id=result.strategy_version_id,
                test_job_id=result.test_job_id,
                result_id=result.result_id,
            ),
        )
        return result

    def record_suggestion_created(
        self,
        *,
        result_id: str,
        suggestion_id: str,
        suggestion_type: str,
        message: str,
    ) -> AiSuggestionRecord:
        result = self._repository.result(result_id)
        if result is None:
            raise ValueError(f"unknown result: {result_id}")
        version = self._repository.version(result.strategy_version_id)
        if version is None:
            raise ValueError(f"unknown strategy version: {result.strategy_version_id}")
        if version.ai_thread_id is None:
            raise ValueError("strategy version is missing ai_thread_id")
        if version.improvement_cycle_id is None:
            raise ValueError("strategy version is missing improvement_cycle_id")
        suggestion = AiSuggestionRecord(
            suggestion_id=suggestion_id,
            project_id=result.project_id,
            strategy_lineage_id=result.strategy_lineage_id,
            strategy_version_id=result.strategy_version_id,
            result_id=result.result_id,
            ai_thread_id=version.ai_thread_id,
            improvement_cycle_id=version.improvement_cycle_id,
            suggestion_type=suggestion_type,
            message=message,
        )
        self._repository.save_ai_suggestion(suggestion)
        self._stream.publish(
            "builder:workflow:events",
            WorkflowEvent(
                event="suggestion.created",
                project_id=suggestion.project_id,
                strategy_lineage_id=suggestion.strategy_lineage_id,
                strategy_version_id=suggestion.strategy_version_id,
                result_id=suggestion.result_id,
                ai_thread_id=suggestion.ai_thread_id,
                improvement_cycle_id=suggestion.improvement_cycle_id,
            ),
        )
        return suggestion
