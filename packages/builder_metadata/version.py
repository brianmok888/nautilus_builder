"""Canonical version source for nautilus_builder.

Reads from installed package metadata when available,
falls back to pyproject.toml for local/source installs.
"""
from __future__ import annotations

import re
from pathlib import Path

_PACKAGE_NAME = "nautilus-builder"
_REPO_ROOT = Path(__file__).resolve().parents[2]


def _read_version_from_pyproject() -> str:
    """Read version from pyproject.toml without requiring tomllib (Python 3.11+)."""
    pyproject = _REPO_ROOT / "pyproject.toml"
    if not pyproject.exists():
        return "0.0.0-unknown"
    text = pyproject.read_text(encoding="utf-8")
    m = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
    return m.group(1) if m else "0.0.0-unknown"


def _read_version_from_metadata() -> str | None:
    """Try to read version from installed package metadata."""
    try:
        import importlib.metadata

        return importlib.metadata.version(_PACKAGE_NAME)
    except importlib.metadata.PackageNotFoundError:
        return None


_cached_version: str | None = None


def get_canonical_version() -> str:
    """Return the single canonical version string for this Builder install."""
    global _cached_version
    if _cached_version is not None:
        return _cached_version

    # Prefer installed metadata, fall back to pyproject.toml
    installed = _read_version_from_metadata()
    if installed is not None:
        _cached_version = installed
        return installed

    _cached_version = _read_version_from_pyproject()
    return _cached_version
