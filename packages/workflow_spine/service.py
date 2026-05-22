from __future__ import annotations

from itertools import count

from packages.workflow_spine.event_stream import InMemoryWorkflowStream
from packages.workflow_spine.models import (
    StrategyIdentity,
    StrategyTestParams,
    StrategyTestWorkflowOutcome,
    StrategyVersionIdentity,
    TestJobRecord,
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
