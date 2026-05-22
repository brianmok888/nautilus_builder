from packages.workflow_spine import (
    FakePostgresWorkflowRepository,
    FakeRedisWorkflowStream,
    InMemoryWorkflowRepository,
    InMemoryWorkflowStream,
    WorkflowEvent,
    assert_postgres_repository_contract,
    assert_redis_stream_contract,
)


def test_in_memory_repository_satisfies_postgres_repository_contract() -> None:
    assert_postgres_repository_contract(InMemoryWorkflowRepository())


def test_fake_postgres_repository_declares_future_adapter_without_db_connection() -> None:
    repository = FakePostgresWorkflowRepository(dsn_name="BUILDER_DATABASE_URL")

    assert repository.dsn_name == "BUILDER_DATABASE_URL"
    assert_postgres_repository_contract(repository)


def test_in_memory_stream_satisfies_redis_stream_contract() -> None:
    assert_redis_stream_contract(InMemoryWorkflowStream())


def test_fake_redis_stream_declares_namespace_without_redis_connection() -> None:
    stream = FakeRedisWorkflowStream(namespace="builder")
    event = WorkflowEvent(
        event="test.enqueued",
        project_id="project_001",
        strategy_lineage_id="lineage_alpha",
        strategy_version_id="sv_001",
    )

    assert stream.namespace == "builder"
    stream.publish("builder:test:jobs", event)
    assert stream.events_for("builder:test:jobs") == [event]
