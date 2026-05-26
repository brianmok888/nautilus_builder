from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MIGRATION = ROOT / "infra" / "migrations" / "004_builder_execution_lane_venue_ui.sql"


def _sql() -> str:
    return MIGRATION.read_text()


def test_execution_lane_venue_ui_migration_links_lane_to_venue_and_features() -> None:
    sql = _sql()

    assert "ALTER TABLE builder.execution_lane_runs" in sql
    assert "ADD COLUMN IF NOT EXISTS adapter_id TEXT" in sql
    assert "ADD COLUMN IF NOT EXISTS venue TEXT" in sql
    assert "ADD COLUMN IF NOT EXISTS venue_account_id TEXT" in sql
    assert "ADD COLUMN IF NOT EXISTS ui_enabled BOOLEAN NOT NULL DEFAULT FALSE" in sql
    assert "ADD COLUMN IF NOT EXISTS paper_controls_enabled BOOLEAN NOT NULL DEFAULT FALSE" in sql
    assert "ADD COLUMN IF NOT EXISTS live_controls_enabled BOOLEAN NOT NULL DEFAULT FALSE" in sql
    assert "execution_lane_runs_enabled_requires_venue" in sql
    assert "execution_lane_runs_live_ui_requires_authority" in sql

    command_block = re.search(r"ALTER TABLE builder\.execution_lane_commands(.*?);", sql, re.DOTALL)
    assert command_block is not None
    assert "ADD COLUMN IF NOT EXISTS adapter_id TEXT" in command_block.group(1)
    assert "ADD COLUMN IF NOT EXISTS venue TEXT" in command_block.group(1)
    assert "execution_lane_commands_require_venue" in sql
    assert "execution_lane_commands_venue_idx" in sql
