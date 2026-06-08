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
from packages.postgres.migrations import apply_migrations  # noqa: E402
from packages.postgres.seed import seed_default_market_data  # noqa: E402
from packages.postgres.strategy_repository import PostgresStrategyRepository  # noqa: E402
from packages.postgres.backtest_job_repository import PostgresBacktestJobRepository  # noqa: E402
from packages.backtest_jobs.postgres_service import PostgresBacktestJobService  # noqa: E402
from packages.strategy_spec.demo_seed import _DEMO_STRATEGIES  # noqa: E402
from packages.strategy_spec.models import (  # noqa: E402
    DataRange,
    IndicatorInput,
    IndicatorSpec,
    IndicatorType,
    Provenance,
    RiskBlock,
    RuleBlock,
    RuleClause,
    StrategySpec,
)
from scripts.seed_demo_evidence import seed_demo_evidence  # noqa: E402


def seed_demo_strategies_pg(conn: object, schema: str = "builder") -> list[str]:
    """Upsert demo strategies into Postgres. Returns list of strategy_ids."""
    repo = PostgresStrategyRepository(conn, schema=schema)
    seeded: list[str] = []

    for strategy_id, name, status, stage, validation, created_from in _DEMO_STRATEGIES:
        spec = StrategySpec(
            strategy_id=strategy_id,
            name=name,
            stage=stage,
            indicators=[
                IndicatorSpec(type=IndicatorType.EMA, input=IndicatorInput.CLOSE, period=20),
                IndicatorSpec(type=IndicatorType.EMA, input=IndicatorInput.CLOSE, period=50),
                IndicatorSpec(type=IndicatorType.RSI, input=IndicatorInput.CLOSE, period=14),
            ],
            long_entry=RuleBlock(all=[
                RuleClause(crossed_above=["ema_fast", "ema_slow"]),
                RuleClause(gt=["rsi", 52]),
            ]),
            long_exit=RuleBlock(any=[
                RuleClause(crossed_below=["ema_fast", "ema_slow"]),
                RuleClause(lt=["rsi", 45]),
            ]),
            risk=RiskBlock(position_size_pct=0.05, stop_loss_pct=0.012, take_profit_pct=0.024, max_hold_bars=48),
            data_range=DataRange(start="2025-01-01T00:00:00Z", end="2025-06-01T00:00:00Z"),
            adapter_id="BINANCE_PERP",
            instrument_id="BTCUSDT-PERP",
            validation=validation,
            provenance=Provenance(created_from=created_from),
        )

        try:
            repo.save_explicit(strategy_id, spec)
        except Exception:
            pass

        conn.execute(
            f"UPDATE {schema}.strategies SET status = %s, updated_at = now() WHERE strategy_id = %s",
            (status.value, strategy_id),
        )
        seeded.append(strategy_id)

    return seeded


def seed_demo_evidence_pg(
    conn: object,
    schema: str = "builder",
) -> dict[str, str]:
    """Seed demo backtest evidence into Postgres using the same seed_demo_evidence logic.

    Returns a mapping of strategy_id -> job_id (or "" if no job created).
    """
    repo = PostgresStrategyRepository(conn, schema=schema)
    bt_repo = PostgresBacktestJobRepository(conn, schema=schema)
    bt_service = PostgresBacktestJobService(bt_repo)

    result = seed_demo_evidence(repo, bt_service)
    return result


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

        seeded = seed_demo_strategies_pg(conn, schema="builder")
        print(f"Seeded {len(seeded)} demo strategies:")
        for sid in seeded:
            print(f"  {sid}")

        evidence = seed_demo_evidence_pg(conn, schema="builder")
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
