import pytest

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


def test_fake_postgres_repository_rejects_literal_network_dsn() -> None:
    with pytest.raises(ValueError, match="Postgres adapter guard requires an env var name"):
        FakePostgresWorkflowRepository(dsn_name="postgresql://localhost/builder")


def test_fake_postgres_repository_rejects_non_url_dsn_shapes() -> None:
    for dsn_name in ["host=localhost dbname=builder", "localhost:5432/builder", "builder-db"]:
        with pytest.raises(ValueError, match="Postgres adapter guard requires an env var name"):
            FakePostgresWorkflowRepository(dsn_name=dsn_name)


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


def test_fake_redis_stream_rejects_literal_network_url_namespace() -> None:
    with pytest.raises(ValueError, match="Redis adapter guard requires a builder namespace"):
        FakeRedisWorkflowStream(namespace="redis://localhost:6379/0")
