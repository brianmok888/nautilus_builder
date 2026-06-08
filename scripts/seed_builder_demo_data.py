#!/usr/bin/env python3
"""Seed Postgres with demo strategies and backtest evidence.

Creates 8 demo strategies covering every lifecycle status, plus demo
backtest jobs with realistic lifecycle states (failed, passed, promotion-ready).

Idempotent: re-running will not duplicate records.

Builder-only safety: no live execution, no trade actions, no submit_order.

Usage:
    export BUILDER_DATABASE_URL="postgresql://builder:builder_dev@localhost:5432/nautilus_builder"
    uv run python scripts/seed_builder_demo_data.py
"""
from __future__ import annotations

import os
import sys

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from packages.postgres.connection import connect  # noqa: E402
from packages.postgres.identifiers import postgres_table, safe_postgres_identifier  # noqa: E402
from packages.postgres.migrations import apply_migrations  # noqa: E402
from packages.postgres.seed import seed_default_market_data  # noqa: E402
from packages.postgres.strategy_repository import PostgresStrategyRepository  # noqa: E402
from packages.postgres.backtest_job_repository import PostgresBacktestJobRepository  # noqa: E402
from packages.auth import UserProjectContext  # noqa: E402
from packages.backtest_jobs.postgres_service import PostgresBacktestJobService  # noqa: E402
from packages.strategy_spec.demo_seed import _DEMO_STRATEGIES, _make_spec  # noqa: E402
from scripts.seed_demo_evidence import seed_demo_evidence  # noqa: E402


def seed_demo_strategies_pg(
    conn: object,
    schema: str = "builder",
    *,
    context: UserProjectContext | None = None,
) -> list[str]:
    """Upsert demo strategies into Postgres. Returns list of strategy_ids."""
    schema = safe_postgres_identifier(schema)
    repo = PostgresStrategyRepository(conn, schema=schema)
    seeded: list[str] = []
    strategies_table = postgres_table(schema, "strategies")

    for strategy_id, name, status, stage, validation, created_from in _DEMO_STRATEGIES:
        spec = _make_spec(name, status, stage, validation, created_from)

        repo.save_explicit(strategy_id, spec, context=context)

        conn.execute(
            f"UPDATE {strategies_table} SET status = %s, updated_at = now() WHERE strategy_id = %s",
            (status.value, strategy_id),
        )
        seeded.append(strategy_id)

    return seeded


def seed_demo_evidence_pg(
    conn: object,
    schema: str = "builder",
    *,
    context: UserProjectContext | None = None,
) -> dict[str, str]:
    """Seed demo backtest evidence into Postgres using the same seed_demo_evidence logic.

    Returns a mapping of strategy_id -> job_id (or "" if no job created).
    """
    safe_schema = safe_postgres_identifier(schema)
    repo = PostgresStrategyRepository(conn, schema=safe_schema)
    bt_repo = PostgresBacktestJobRepository(conn, schema=safe_schema)
    bt_service = PostgresBacktestJobService(bt_repo)

    result = seed_demo_evidence(repo, bt_service, context=context)
    return result


def _demo_seed_context() -> UserProjectContext:
    return UserProjectContext(
        user_id=os.environ.get("BUILDER_DEV_USER_ID", "local_user"),
        project_id=os.environ.get("BUILDER_DEV_PROJECT_ID", "local_project"),
        role=os.environ.get("BUILDER_DEV_ROLE", "builder"),
    )


def main() -> int:
    dsn = os.environ.get("BUILDER_DATABASE_URL", "").strip()
    if not dsn:
        print("Error: BUILDER_DATABASE_URL is not set.", file=sys.stderr)
        print('Example: export BUILDER_DATABASE_URL="postgresql://builder:builder_dev@localhost:5432/nautilus_builder"', file=sys.stderr)
        return 1

    conn = connect(dsn)
    try:
        applied = apply_migrations(conn, schema="builder")
        if applied:
            print(f"Applied {len(applied)} migration(s):")
            for name in applied:
                print(f"  {name}")

        seed_default_market_data(conn, schema="builder")
        print("Seeded adapter and instrument data.")

        seed_context = _demo_seed_context()
        seeded = seed_demo_strategies_pg(conn, schema="builder", context=seed_context)
        print(f"Seeded {len(seeded)} demo strategies:")
        for sid in seeded:
            print(f"  {sid}")

        evidence = seed_demo_evidence_pg(conn, schema="builder", context=seed_context)
        if evidence:
            print(f"Seeded {len(evidence)} demo backtest jobs:")
            for strategy_id, job_id in evidence.items():
                print(f"  {strategy_id}: {job_id or '(no job)'}")

        row = conn.execute("SELECT COUNT(*) FROM builder.strategies").fetchone()
        count = row[0] if row else 0
        print(f"\nTotal strategies in DB: {count}")

        bt_row = conn.execute("SELECT COUNT(*) FROM builder.backtest_jobs").fetchone()
        bt_count = bt_row[0] if bt_row else 0
        print(f"Total backtest jobs in DB: {bt_count}")

    finally:
        conn.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
