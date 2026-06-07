"""Tests for migration v2: promotion ledger, audit events, compiler/replay runs."""
from __future__ import annotations


from packages.postgres.migrations import MIGRATIONS


class TestMigrationV2:
    def test_migration_v2_exists(self):
        versions = [m.version for m in MIGRATIONS]
        assert 2 in versions, f"Migration v2 not found. Versions: {versions}"

    def test_migration_v2_has_name(self):
        v2 = [m for m in MIGRATIONS if m.version == 2][0]
        assert "promotion" in v2.name.lower() or "evidence" in v2.name.lower() or "ledger" in v2.name.lower()

    def test_migration_v2_creates_promotion_ledger(self):
        v2 = [m for m in MIGRATIONS if m.version == 2][0]
        assert "promotion_ledger" in v2.up

    def test_migration_v2_creates_audit_events(self):
        v2 = [m for m in MIGRATIONS if m.version == 2][0]
        assert "audit_events" in v2.up

    def test_migration_v2_creates_compiler_runs(self):
        v2 = [m for m in MIGRATIONS if m.version == 2][0]
        assert "compiler_runs" in v2.up

    def test_migration_v2_creates_replay_runs(self):
        v2 = [m for m in MIGRATIONS if m.version == 2][0]
        assert "replay_runs" in v2.up

    def test_migration_v2_has_down(self):
        v2 = [m for m in MIGRATIONS if m.version == 2][0]
        assert v2.down is not None
        assert len(v2.down.strip()) > 0

    def test_migration_v2_promotion_ledger_has_required_columns(self):
        v2 = [m for m in MIGRATIONS if m.version == 2][0]
        required = [
            "strategy_spec_hash",
            "compiler_hash",
            "policy_hash",
            "dataset_hash",
            "replay_report_hash",
            "artifact_hash",
            "promotion_mode",
        ]
        for col in required:
            assert col in v2.up, f"promotion_ledger missing column: {col}"

    def test_migration_v2_audit_events_has_required_columns(self):
        v2 = [m for m in MIGRATIONS if m.version == 2][0]
        required = ["request_id", "actor_id", "action", "resource_type", "status"]
        for col in required:
            assert col in v2.up, f"audit_events missing column: {col}"
