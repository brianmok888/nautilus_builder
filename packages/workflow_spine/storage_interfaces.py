from __future__ import annotations

import re
from typing import Protocol, runtime_checkable

from packages.workflow_spine.event_stream import InMemoryWorkflowStream
from packages.workflow_spine.models import AiSuggestionRecord, StrategyIdentity, StrategyVersionIdentity, WorkflowJobRecord, WorkflowResultRecord, WorkflowEvent
from packages.workflow_spine.repository import InMemoryWorkflowRepository


@runtime_checkable
class WorkflowRepositoryProtocol(Protocol):
    def save_strategy(self, strategy: StrategyIdentity) -> None: ...
    def save_version(self, version: StrategyVersionIdentity) -> None: ...
    def save_job(self, job: WorkflowJobRecord) -> None: ...
    def save_result(self, result: WorkflowResultRecord) -> None: ...
    def save_ai_suggestion(self, suggestion: AiSuggestionRecord) -> None: ...
    def strategy(self, strategy_id: str) -> StrategyIdentity | None: ...
    def version(self, strategy_version_id: str) -> StrategyVersionIdentity | None: ...
    def job(self, test_job_id: str) -> WorkflowJobRecord | None: ...
    def result(self, result_id: str) -> WorkflowResultRecord | None: ...


@runtime_checkable
class WorkflowStreamProtocol(Protocol):
    def publish(self, stream_name: str, event: WorkflowEvent) -> None: ...
    def events_for(self, stream_name: str) -> list[WorkflowEvent]: ...


class FakePostgresWorkflowRepository(InMemoryWorkflowRepository):
    def __init__(self, *, dsn_name: str) -> None:
        if re.fullmatch(r"[A-Z_][A-Z0-9_]*", dsn_name) is None:
            raise ValueError("Postgres adapter guard requires an env var name, not a network DSN")
        super().__init__()
        self.dsn_name = dsn_name


class FakeRedisWorkflowStream(InMemoryWorkflowStream):
    def __init__(self, *, namespace: str) -> None:
        if "://" in namespace or namespace != "builder":
            raise ValueError("Redis adapter guard requires a builder namespace, not a network URL")
        super().__init__()
        self.namespace = namespace


def assert_postgres_repository_contract(repository: WorkflowRepositoryProtocol) -> None:
    required = [
        "save_strategy",
        "save_version",
        "save_job",
        "save_result",
        "save_ai_suggestion",
        "strategy",
        "version",
        "job",
        "result",
    ]
    for name in required:
        if not callable(getattr(repository, name, None)):
            raise AssertionError(f"repository missing {name}")


def assert_redis_stream_contract(stream: WorkflowStreamProtocol) -> None:
    required = ["publish", "events_for"]
    for name in required:
        if not callable(getattr(stream, name, None)):
            raise AssertionError(f"stream missing {name}")
