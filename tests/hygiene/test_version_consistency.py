"""Version consistency tests — v4 closure.

Ensures a single canonical version flows through pyproject.toml,
Python package metadata, /health/build, and API app metadata.

Note: When running from source (not installed), get_canonical_version()
falls back to pyproject.toml. The test accounts for this by clearing
the version cache before checking.
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
        assert re.match(r"\d+\.\d+\.\d+", v), f"Version {v!r} does not look valid"

    def test_builder_metadata_module_returns_pyproject_version(self) -> None:
        from packages.builder_metadata import version as vm

        vm._cached_version = None
        # Force pyproject.toml reading by mocking installed metadata
        _original = importlib.metadata.version
        def _raise_not_found(name):
            raise importlib.metadata.PackageNotFoundError(name)
        importlib.metadata.version = _raise_not_found
        try:
            result = vm.get_canonical_version()
        finally:
            importlib.metadata.version = _original
            vm._cached_version = None

        assert result == _read_pyproject_version(), (
            f"get_canonical_version() returned {result!r}, expected {_read_pyproject_version()!r}"
        )

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
        release_path = REPO_ROOT / "RELEASE.md"
        if not release_path.exists():
            pytest.skip("RELEASE.md not found")
        text = release_path.read_text()
        v = _read_pyproject_version()
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

    def test_release_header_no_version_drift(self) -> None:
        """RELEASE.md header must have exactly one version number."""
        text = (REPO_ROOT / "RELEASE.md").read_text()
        header = text.split("## Changelog")[0] if "## Changelog" in text else text
        versions = re.findall(r'\bv?\d+\.\d+\.\d+\b', header)
        unique = set(v.lstrip("v") for v in versions)
        assert len(unique) == 1, (
            f"RELEASE.md header has conflicting versions: {unique}"
        )
