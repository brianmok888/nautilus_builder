from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MIGRATION = ROOT / "infra" / "migrations" / "003_builder_execution_lane.sql"


def _sql() -> str:
    return MIGRATION.read_text()


def _table_block(sql: str, table: str) -> str:
    pattern = rf"CREATE TABLE IF NOT EXISTS builder\.{re.escape(table)}\s*\((.*?)\n\);"
    match = re.search(pattern, sql, re.IGNORECASE | re.DOTALL)
    assert match, f"builder.{table} table is missing"
    return match.group(1)


def test_execution_lane_migration_adds_standalone_lane_tables() -> None:
    sql = _sql()

    assert "Nautilus-Daedalus" not in sql
    assert "CREATE SCHEMA IF NOT EXISTS builder" in sql
    for table in ("execution_lane_runs", "execution_lane_commands", "execution_lane_reports", "execution_lane_heartbeats"):
        _table_block(sql, table)

    runs = _table_block(sql, "execution_lane_runs")
    assert "strategy_lane_coupled BOOLEAN NOT NULL DEFAULT FALSE" in runs
    assert "lane_mode IN ('paper', 'live')" in runs
    assert "live_authority_requires_activation" in runs
    assert "credential_slot_ref" in runs
    assert "reconciliation_required" in runs

    commands = _table_block(sql, "execution_lane_commands")
    assert "idempotency_key TEXT NOT NULL" in commands
    assert "strategy_lane_coupled BOOLEAN NOT NULL DEFAULT FALSE" in commands
    assert "trade_action_id TEXT NOT NULL" in commands
    assert "order_intent JSONB NOT NULL" in commands
    assert "execution_command_submit_requires_live_authority" in commands
    assert "UNIQUE (runtime_profile_id, idempotency_key)" in commands

    reports = _table_block(sql, "execution_lane_reports")
    assert "report_type TEXT NOT NULL" in reports
    assert "execution_report_id TEXT" in reports
    assert "payload JSONB NOT NULL" in reports
