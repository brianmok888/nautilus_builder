from __future__ import annotations

from collections.abc import Callable
from typing import Any
from unittest.mock import MagicMock

import pytest

from packages.postgres.adapter_repository import PostgresAdapterRepository
from packages.postgres.backtest_job_repository import PostgresBacktestJobRepository
from packages.postgres.config_repository import PostgresConfigRepository
from packages.postgres.migrations import apply_migrations, current_version, ensure_schema, rollback
from packages.postgres.promotion_ledger_repository import PromotionLedgerRepository
from packages.postgres.strategy_repository import PostgresStrategyRepository
from packages.postgres.workflow_result_repository import PostgresWorkflowResultRepository
from packages.postgres.seed import seed_default_market_data


UNSAFE_SCHEMA = "builder;drop schema public"


RepositoryFactory = Callable[[Any, str], object]


@pytest.mark.parametrize(
    "factory",
    [
        lambda conn, schema: PostgresAdapterRepository(conn, schema=schema),
        lambda conn, schema: PostgresBacktestJobRepository(conn, schema=schema),
        lambda conn, schema: PostgresConfigRepository(conn, schema=schema),
        lambda conn, schema: PromotionLedgerRepository(conn, schema=schema),
        lambda conn, schema: PostgresStrategyRepository(conn, schema=schema),
        lambda conn, schema: PostgresWorkflowResultRepository(conn, schema=schema),
    ],
)
def test_postgres_repositories_reject_unsafe_schema_identifiers(
    factory: RepositoryFactory,
) -> None:
    with pytest.raises(ValueError, match="Postgres identifier"):
        factory(MagicMock(), UNSAFE_SCHEMA)


@pytest.mark.parametrize("operation", [ensure_schema, current_version, apply_migrations, rollback])
def test_migration_entrypoints_reject_unsafe_schema_identifiers(
    operation: Callable[..., object],
) -> None:
    conn = MagicMock()

    with pytest.raises(ValueError, match="Postgres identifier"):
        operation(conn, schema=UNSAFE_SCHEMA)

    conn.execute.assert_not_called()


def test_seed_default_market_data_rejects_unsafe_schema_identifier() -> None:
    conn = MagicMock()

    with pytest.raises(ValueError, match="Postgres identifier"):
        seed_default_market_data(conn, schema=UNSAFE_SCHEMA)

    conn.execute.assert_not_called()
