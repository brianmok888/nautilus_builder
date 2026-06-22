"""Baseline representing the current Nautilus Builder schema.

Revision ID: 0001_baseline_current_schema
Revises:
Create Date: 2026-06-22

This baseline captures the schema state produced by the existing custom
migration runner (packages/postgres/migrations.py) as of 2026-06-22, which
applies these 7 custom migrations:
  1. initial_schema
  2. promotion_ledger_and_audit
  3. audit_events_project_id
  4. builder_backtest_and_config_tables
  5. strategy_scope_columns
  6. audit_events_project_id_not_null
  7. evidence_refs_table

This revision is a STAMP-ONLY baseline: existing deployments run
``alembic stamp head`` once to record that they are already at this state.
The upgrade()/downgrade() are intentionally no-ops because the schema was
created by the custom runner; Alembic must not re-apply or drop it.

NEW migrations after this baseline are written as Alembic revisions (raw SQL
via op.execute()) and become the source of truth going forward.
"""
from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = "0001_baseline_current_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # No-op: schema is managed by the existing custom runner.
    # Existing deployments: `alembic stamp head` to mark current state.
    pass


def downgrade() -> None:
    # No-op: do not drop schema managed by the custom runner.
    pass
