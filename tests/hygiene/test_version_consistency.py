"""Version consistency tests — Segment 1.

Ensures a single canonical version flows through pyproject.toml,
Python package metadata, /health/build, and API app metadata.
"""
import importlib.metadata
import json
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


def _read_pyproject_version() -> str:
    """Read version directly from pyproject.toml without TOML dependency."""
    pyproject = REPO_ROOT / "pyproject.toml"
    text = pyproject.read_text()
    m = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
    assert m, "No version found in pyproject.toml"
    return m.group(1)


class TestVersionConsistency:
    """One canonical version must flow everywhere."""

    def test_pyproject_version_is_valid_semver(self) -> None:
        v = _read_pyproject_version()
        # Accept PEP 440 / semver-like versions
        assert re.match(r"\d+\.\d+\.\d+", v), f"Version {v!r} does not look valid"

    def test_builder_metadata_module_returns_pyproject_version(self) -> None:
        from packages.builder_metadata.version import get_canonical_version

        assert get_canonical_version() == _read_pyproject_version()

    def test_health_build_returns_canonical_version(self) -> None:
        from packages.builder_metadata.version import get_canonical_version

        from services.api.fastapi_app import create_fastapi_app

        app = create_fastapi_app(
            artifact_store=None,
            rate_limiter=None,
        )
        client = pytest.importorskip("fastapi.testclient").TestClient(app)
        resp = client.get("/health/build")
        assert resp.status_code == 200
        body = resp.json()
        assert body["version"] == get_canonical_version(), (
            f"/health/build version {body['version']!r} != canonical {get_canonical_version()!r}"
        )

    def test_fastapi_app_metadata_uses_canonical_version(self) -> None:
        from packages.builder_metadata.version import get_canonical_version

        from services.api.fastapi_app import create_fastapi_app

        app = create_fastapi_app(
            artifact_store=None,
            rate_limiter=None,
        )
        assert app.version == get_canonical_version(), (
            f"FastAPI app.version {app.version!r} != canonical {get_canonical_version()!r}"
        )

    def test_release_md_mentions_canonical_version_or_unreleased(self) -> None:
        """RELEASE.md must either reference the current version or be explicitly unreleased."""
        release_path = REPO_ROOT / "RELEASE.md"
        if not release_path.exists():
            pytest.skip("RELEASE.md not found")
        text = release_path.read_text()
        v = _read_pyproject_version()
        # Either the version appears in the doc or it says unreleased
        assert v in text or "unreleased" in text.lower(), (
            f"RELEASE.md does not mention version {v!r} and is not marked unreleased"
        )

    def test_changelog_mentions_canonical_version_or_unreleased(self) -> None:
        changelog_path = REPO_ROOT / "CHANGELOG.md"
        if not changelog_path.exists():
            pytest.skip("CHANGELOG.md not found")
        text = changelog_path.read_text()
        v = _read_pyproject_version()
        assert v in text or "unreleased" in text.lower(), (
            f"CHANGELOG.md does not mention version {v!r} and is not marked unreleased"
        )
