from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from packages.auth import UserProjectContext
from packages.postgres.strategy_repository import PostgresStrategyRepository
from tests.strategy_spec.test_schema_valid import make_valid_spec
from packages.strategy_spec.models import StrategySpec


class _PsycopgLikeTransaction:
    def __enter__(self) -> "_PsycopgLikeTransaction":
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> bool:
        return False


def _context() -> UserProjectContext:
    return UserProjectContext(user_id="user_123", project_id="project_alpha")


def _spec() -> StrategySpec:
    return StrategySpec.model_validate(make_valid_spec())


def test_save_persists_strategy_scope_columns() -> None:
    conn = MagicMock()
    conn.transaction.return_value = _PsycopgLikeTransaction()
    conn.execute.return_value.fetchone.return_value = (0,)
    repo = PostgresStrategyRepository(conn)

    repo.save(_spec(), context=_context())

    strategies_call = conn.execute.call_args_list[1]
    versions_call = conn.execute.call_args_list[2]
    assert "user_id" in strategies_call.args[0]
    assert "project_id" in strategies_call.args[0]
    assert strategies_call.args[1][-2:] == ("user_123", "project_alpha")
    assert "user_id" in versions_call.args[0]
    assert "project_id" in versions_call.args[0]
    assert versions_call.args[1][-2:] == ("user_123", "project_alpha")


def test_save_explicit_uses_connection_execute_inside_transaction() -> None:
    conn = MagicMock()
    conn.transaction.return_value = _PsycopgLikeTransaction()
    repo = PostgresStrategyRepository(conn)

    repo.save_explicit("strategy_explicit", _spec(), context=_context())

    assert conn.transaction.called
    assert len(conn.execute.call_args_list) == 2
    strategies_call = conn.execute.call_args_list[0]
    versions_call = conn.execute.call_args_list[1]
    assert "ON CONFLICT (strategy_id)" in strategies_call.args[0]
    assert strategies_call.args[1][-2:] == ("user_123", "project_alpha")
    assert "ON CONFLICT (strategy_version_id)" in versions_call.args[0]
    assert versions_call.args[1][-2:] == ("user_123", "project_alpha")


def test_list_filters_by_user_project_context() -> None:
    conn = MagicMock()
    conn.execute.return_value.fetchall.return_value = []
    repo = PostgresStrategyRepository(conn)

    repo.list(context=_context())

    sql, params = conn.execute.call_args.args
    assert "WHERE user_id = %s AND project_id = %s" in " ".join(sql.split())
    assert params == ("user_123", "project_alpha")


def test_approve_strategy_accepts_and_applies_scope_context() -> None:
    conn = MagicMock()
    conn.execute.return_value.fetchone.side_effect = [("backtested",), ("strategy_001", "lineage_strategy_001", "approved", "{}", "user_123", "project_alpha"), (1,)]
    repo = PostgresStrategyRepository(conn)

    result = repo.approve_strategy("strategy_001", context=_context())

    assert result is not None
    assert result["status"] == "approved"
    approval_sql, approval_params = conn.execute.call_args_list[0].args
    assert "user_id = %s" in approval_sql
    assert "project_id = %s" in approval_sql
    assert approval_params == ("strategy_001", "user_123", "project_alpha")


@pytest.mark.parametrize("migration_sql", [m.up for m in __import__("packages.postgres.migrations", fromlist=["MIGRATIONS"]).MIGRATIONS])
def test_strategy_migrations_include_scope_columns(migration_sql: str) -> None:
    if "CREATE TABLE IF NOT EXISTS {schema}.strategies" not in migration_sql:
        return
    assert "user_id" in migration_sql
    assert "project_id" in migration_sql
