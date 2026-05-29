from packages.workflow_spine.event_stream import InMemoryWorkflowStream, InvalidStreamNamespaceError
from packages.workflow_spine.models import (
    AiSuggestionRecord,
    StrategyIdentity,
    StrategyTestParams,
    StrategyTestWorkflowOutcome,
    StrategyVersionIdentity,
    WorkflowJobRecord,
    WorkflowResultRecord,
    WorkflowEvent,
)
from packages.workflow_spine.repository import InMemoryWorkflowRepository
from packages.workflow_spine.projections import WorkflowReadModel
from packages.workflow_spine.postgres_repository import SqliteWorkflowRepository, workflow_schema_statements


# DEPRECATED: PostgresWorkflowRepository alias. Use SqliteWorkflowRepository.
# Will be removed after 2026-07-01.
def __getattr__(name: str) -> type:
    import warnings
    import packages.workflow_spine.postgres_repository as _pr
    if name == "PostgresWorkflowRepository":
        return _pr.PostgresWorkflowRepository
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
from packages.workflow_spine.postgres_runtime import connect_builder_postgres
from packages.workflow_spine.service import StrategyTestWorkflowService
from packages.workflow_spine.storage_config import BuilderPostgresConfig, BuilderRedisConfig
from packages.workflow_spine.storage_interfaces import (
    FakePostgresWorkflowRepository,
    FakeRedisWorkflowStream,
    WorkflowRepositoryProtocol,
    WorkflowStreamProtocol,
    assert_postgres_repository_contract,
    assert_redis_stream_contract,
)

__all__ = [
    "StrategyIdentity",
    "StrategyVersionIdentity",
    "WorkflowEvent",
    "InMemoryWorkflowStream",
    "InvalidStreamNamespaceError",
    "AiSuggestionRecord",
    "InMemoryWorkflowRepository",
    "WorkflowReadModel",
    # "PostgresWorkflowRepository" deprecated; use SqliteWorkflowRepository
    "SqliteWorkflowRepository",
    "workflow_schema_statements",
    "connect_builder_postgres",
    "StrategyTestParams",
    "StrategyTestWorkflowOutcome",
    "StrategyTestWorkflowService",
    "WorkflowJobRecord",
    "WorkflowResultRecord",
    "FakePostgresWorkflowRepository",
    "FakeRedisWorkflowStream",
    "WorkflowRepositoryProtocol",
    "WorkflowStreamProtocol",
    "BuilderPostgresConfig",
    "BuilderRedisConfig",
    "assert_postgres_repository_contract",
    "assert_redis_stream_contract",
]
