"""Tests verifying legacy items have been removed (Segment 15 closure)."""
from __future__ import annotations

import os
import warnings
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


class TestPostgresWorkflowRepositoryAliasRemoved:
    """The PostgresWorkflowRepository deprecation alias is removed."""

    def test_postgres_repository_has_no_alias(self) -> None:
        import packages.workflow_spine.postgres_repository as pr_mod
        assert not hasattr(pr_mod, "PostgresWorkflowRepository")

    def test_init_has_no_alias(self) -> None:
        import packages.workflow_spine as ws_mod
        assert not hasattr(ws_mod, "PostgresWorkflowRepository")

    def test_init_all_exports_no_alias(self) -> None:
        import packages.workflow_spine as ws_mod
        assert "PostgresWorkflowRepository" not in ws_mod.__all__


class TestLegacyCompileHashRemoved:
    """The legacy compile hash derivation env escape is removed."""

    def test_backtest_jobs_no_legacy_env(self) -> None:
        content = (REPO_ROOT / "services" / "api" / "routes" / "backtest_jobs.py").read_text()
        assert "USE_LEGACY_COMPILE_HASH" not in content
        assert "legacy" not in content.lower() or "legacy" in content.lower() and "removed" in content.lower()


class TestAllowLegacyFixtureRefsRemoved:
    """The allow_legacy_fixture_refs flag is removed from production code."""

    def test_promotions_no_legacy_flag(self) -> None:
        content = (REPO_ROOT / "services" / "api" / "routes" / "promotions.py").read_text()
        assert "allow_legacy_fixture_refs" not in content

    def test_pyproject_no_legacy_warning_suppression(self) -> None:
        content = (REPO_ROOT / "pyproject.toml").read_text()
        assert "allow_legacy_fixture_refs" not in content


class TestRes001FixtureFallbackRemoved:
    """The res_001 fixture fallback is removed."""

    def test_workflow_results_no_fixture_fallback(self) -> None:
        content = (REPO_ROOT / "services" / "api" / "routes" / "workflow_results.py").read_text()
        assert "res_001" not in content
        assert "BUILDER_ALLOW_FIXTURE_FALLBACK" not in content
        assert "fixture_dev_only" not in content
        assert "allow_fixture_fallback" not in content


class TestStorageConfigNoDeprecationComment:
    """storage_config.py no longer carries stale deprecation comments."""

    def test_storage_config_no_deprecated_header(self) -> None:
        content = (REPO_ROOT / "packages" / "workflow_spine" / "storage_config.py").read_text()
        # The file itself is still used; just the DEPRECATED header should be gone
        lines = content.split("\n")
        for line in lines[:5]:
            assert "DEPRECATED" not in line
            assert "legacy alias" not in line.lower()
