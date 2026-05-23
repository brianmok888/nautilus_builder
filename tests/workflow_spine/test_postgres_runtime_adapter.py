from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest

from packages.workflow_spine.postgres_runtime import connect_builder_postgres


ROOT = Path(__file__).resolve().parents[2]


def test_postgres_migration_defines_builder_owned_runtime_tables() -> None:
    migration = (ROOT / "infra" / "migrations" / "001_builder_workflow_storage.sql").read_text()

    assert "CREATE SCHEMA IF NOT EXISTS builder" in migration
    assert "builder.strategy_identities" in migration
    assert "builder.strategy_versions" in migration
    assert "builder.test_jobs" in migration
    assert "builder.test_results" in migration
    assert "builder.ai_suggestions" in migration
    assert "builder.runtime_events" in migration


def test_postgres_runtime_connects_using_env_owned_dsn(monkeypatch) -> None:
    calls: list[str] = []

    def connect(dsn: str):
        calls.append(dsn)
        return object()

    monkeypatch.setenv("BUILDER_DATABASE_URL", "postgresql://builder@example/builder")
    monkeypatch.setitem(sys.modules, "psycopg", types.SimpleNamespace(connect=connect))

    connection = connect_builder_postgres("BUILDER_DATABASE_URL")

    assert connection is not None
    assert calls == ["postgresql://builder@example/builder"]


def test_postgres_runtime_rejects_missing_dsn_configuration(monkeypatch) -> None:
    monkeypatch.delenv("BUILDER_DATABASE_URL", raising=False)

    with pytest.raises(ValueError, match="Postgres DSN environment variable is not configured"):
        connect_builder_postgres("BUILDER_DATABASE_URL")
