"""Tests for version/release metadata consistency — Segment B v4.

Verifies that pyproject.toml, RELEASE.md, and /health/build agree.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]


def _read_pyproject_version() -> str:
    text = (_REPO_ROOT / "pyproject.toml").read_text()
    m = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
    return m.group(1) if m else "NOT_FOUND"


def _read_release_current_version() -> str:
    """Extract the current release version from RELEASE.md header section."""
    text = (_REPO_ROOT / "RELEASE.md").read_text()
    # Only look in the "Current Release" section (before any changelog)
    header = text.split("## Changelog")[0] if "## Changelog" in text else text
    m = re.search(r'^\*\*Version:\*\*\s*(\S+)', header, re.MULTILINE)
    if m:
        return m.group(1).strip()
    return "NOT_FOUND"


class TestVersionConsistency:
    """Verify version strings agree across all sources."""

    def test_pyproject_version_is_semver(self) -> None:
        version = _read_pyproject_version()
        assert re.match(r"^\d+\.\d+\.\d+$", version), (
            f"pyproject.toml version '{version}' is not semver"
        )

    def test_release_current_version_matches_pyproject(self) -> None:
        pyproject_v = _read_pyproject_version()
        release_v = _read_release_current_version()
        assert release_v == pyproject_v, (
            f"RELEASE.md current version '{release_v}' != pyproject.toml version '{pyproject_v}'"
        )

    def test_health_build_matches_pyproject(self) -> None:
        from packages.builder_metadata import version as vm

        # Force re-read from pyproject.toml since we're testing source consistency
        vm._cached_version = None
        # Clear any installed metadata to force pyproject fallback
        import importlib.metadata
        original = importlib.metadata.version
        def _mock_version(name):
            raise importlib.metadata.PackageNotFoundError(name)
        importlib.metadata.version = _mock_version
        try:
            canonical_v = vm.get_canonical_version()
        finally:
            importlib.metadata.version = original
            vm._cached_version = None

        pyproject_v = _read_pyproject_version()
        assert canonical_v == pyproject_v, (
            f"/health/build version '{canonical_v}' != pyproject.toml version '{pyproject_v}'"
        )

    def test_release_header_has_no_version_drift(self) -> None:
        """RELEASE.md header must not contain conflicting version numbers."""
        text = (_REPO_ROOT / "RELEASE.md").read_text()
        header = text.split("## Changelog")[0] if "## Changelog" in text else text
        versions = re.findall(r'\bv?\d+\.\d+\.\d+\b', header)
        unique = set(v.lstrip("v") for v in versions)
        assert len(unique) == 1, (
            f"RELEASE.md header contains conflicting version numbers: {unique}"
        )


class TestReadinessMatrix:
    """Verify readiness matrix completeness per Segment A v4."""

    def test_readiness_matrix_covers_all_builder_capabilities(self) -> None:
        from packages.readiness.service import get_readiness_matrix

        matrix = get_readiness_matrix()
        capabilities = {e.capability for e in matrix.entries}

        required = {
            "strategy_authoring",
            "strategy_validation",
            "strategy_compiler",
            "synthetic_backtest",
            "real_dataset_replay",
            "promotion_contracts",
            "live_execution",
            "nd_runtime_changes",
            "production_deployment",
            "ai_advisory",
        }
        missing = required - capabilities
        assert not missing, f"Readiness matrix missing capabilities: {missing}"

    def test_live_execution_is_out_of_scope(self) -> None:
        from packages.readiness.models import ReadinessStatus
        from packages.readiness.service import get_readiness_matrix

        matrix = get_readiness_matrix()
        live = [e for e in matrix.entries if e.capability == "live_execution"]
        assert len(live) == 1, "Must have exactly one live_execution entry"
        assert live[0].status == ReadinessStatus.OUT_OF_SCOPE

    def test_nd_runtime_changes_is_out_of_scope(self) -> None:
        from packages.readiness.models import ReadinessStatus
        from packages.readiness.service import get_readiness_matrix

        matrix = get_readiness_matrix()
        nd = [e for e in matrix.entries if e.capability == "nd_runtime_changes"]
        assert len(nd) == 1, "Must have exactly one nd_runtime_changes entry"
        assert nd[0].status == ReadinessStatus.OUT_OF_SCOPE

    def test_readiness_json_export(self) -> None:
        """Matrix must be exportable to JSON for doc/readiness_status.json."""
        from packages.readiness.service import get_readiness_matrix

        matrix = get_readiness_matrix()
        json_str = matrix.model_dump_json()
        assert len(json_str) > 100  # Non-trivial output

    def test_readiness_matrix_property_live_execution_not_ready(self) -> None:
        from packages.readiness.service import get_readiness_matrix

        matrix = get_readiness_matrix()
        assert not matrix.live_execution_ready
