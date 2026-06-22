"""Smoke tests for the Alembic baseline (Adoption Report §3.4 Phase 1).

Validates that Alembic recognizes the baseline revision and that the migration
scaffolding is structurally sound. These are config/smoke tests (no live DB).
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _alembic(*args: str, env_url: str = "postgresql://test:test@localhost:5432/test") -> str:
    env = {**os.environ, "BUILDER_DATABASE_URL": env_url}
    result = subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
    )
    assert result.returncode == 0, f"alembic {' '.join(args)} failed:\n{result.stderr}"
    return result.stdout


def test_alembic_baseline_is_head() -> None:
    """The single baseline revision must be the recognized head."""
    out = _alembic("heads")
    assert "0001_baseline_current_schema" in out


def test_alembic_history_shows_single_baseline() -> None:
    """History must show base -> baseline (linear, no branches)."""
    out = _alembic("history")
    assert "0001_baseline_current_schema" in out
    assert "<base> -> 0001_baseline_current_schema" in out


def test_alembic_offline_upgrade_generates_version_table() -> None:
    """Offline SQL generation must produce the alembic_version table + stamp."""
    out = _alembic("upgrade", "head", "--sql")
    assert "CREATE TABLE alembic_version" in out
    assert "0001_baseline_current_schema" in out


def test_alembic_config_uses_separate_version_table() -> None:
    """The version_table must be 'alembic_version' (separate from custom runner's table)."""
    ini = (REPO_ROOT / "alembic.ini").read_text()
    assert "version_table = alembic_version" in ini


def test_custom_runner_still_present() -> None:
    """Phase 1 dual-run: the existing custom migration runner must remain."""
    assert (REPO_ROOT / "packages" / "postgres" / "migrations.py").exists()
    assert (REPO_ROOT / "scripts" / "apply_builder_migrations.py").exists()
