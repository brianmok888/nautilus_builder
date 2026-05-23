from packages.workflow_spine.event_stream import InMemoryWorkflowStream, InvalidStreamNamespaceError
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
from packages.workflow_spine.projections import WorkflowReadModel
from packages.workflow_spine.postgres_repository import PostgresWorkflowRepository, workflow_schema_statements
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
    "PostgresWorkflowRepository",
    "workflow_schema_statements",
    "connect_builder_postgres",
    "StrategyTestParams",
    "StrategyTestWorkflowOutcome",
    "StrategyTestWorkflowService",
    "TestJobRecord",
    "TestResultRecord",
    "FakePostgresWorkflowRepository",
    "FakeRedisWorkflowStream",
    "WorkflowRepositoryProtocol",
    "WorkflowStreamProtocol",
    "BuilderPostgresConfig",
    "BuilderRedisConfig",
    "assert_postgres_repository_contract",
    "assert_redis_stream_contract",
]
