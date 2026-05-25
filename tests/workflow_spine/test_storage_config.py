import pytest

from packages.workflow_spine import BuilderPostgresConfig, BuilderRedisConfig


def test_builder_postgres_config_uses_builder_db_schema_and_env_name() -> None:
    config = BuilderPostgresConfig(dsn_env="BUILDER_DATABASE_URL", db_schema="builder")

    assert config.dsn_env == "BUILDER_DATABASE_URL"
    assert config.db_schema == "builder"
    assert config.table_name("strategy_versions") == "builder.strategy_versions"


def test_builder_postgres_config_accepts_legacy_schema_alias_without_shadow_field() -> None:
    config = BuilderPostgresConfig(dsn_env="BUILDER_DATABASE_URL", schema="builder")

    assert config.db_schema == "builder"
    assert "db_schema" in config.model_dump()
    assert "schema" not in BuilderPostgresConfig.model_fields


def test_builder_redis_config_uses_builder_namespace_on_shared_redis() -> None:
    config = BuilderRedisConfig(url_env="REDIS_URL", namespace="builder")

    assert config.url_env == "REDIS_URL"
    assert config.stream("workflow:events") == "builder:workflow:events"
    assert config.stream("nd:advisory") == "builder:nd:advisory"


def test_builder_redis_config_rejects_nd_owned_namespace() -> None:
    with pytest.raises(ValueError, match="Builder Redis namespace must not be nd"):
        BuilderRedisConfig(url_env="REDIS_URL", namespace="nd")
