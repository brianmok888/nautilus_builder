"""Tests for canonical version source and build info resolution."""
from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from packages.builder_metadata.build_info import resolve_build_info
from packages.builder_metadata.models import BuilderBuildInfo
from packages.builder_metadata.version import (
    _cached_version,
    _read_version_from_pyproject,
    get_canonical_version,
)


class TestCanonicalVersion:
    """Verify version resolution logic."""

    def test_get_canonical_version_returns_string(self):
        version = get_canonical_version()
        assert isinstance(version, str)
        assert len(version) > 0

    def test_pyproject_fallback_returns_valid_version(self):
        version = _read_version_from_pyproject()
        assert version != "0.0.0-unknown"
        # Should match semver pattern
        parts = version.split(".")
        assert len(parts) >= 2


class TestBuilderBuildInfo:
    """Verify BuilderBuildInfo model constraints."""

    def test_build_info_from_pyproject_source(self):
        info = resolve_build_info()
        assert isinstance(info, BuilderBuildInfo)
        assert info.version != "0.0.0-unknown"
        assert info.source in ("installed_metadata", "pyproject")

    def test_build_info_env_injected_git_metadata(self):
        with patch.dict(os.environ, {
            "BUILDER_GIT_COMMIT": "abc1234",
            "BUILDER_GIT_BRANCH": "feat/test",
            "BUILDER_BUILD_TIME_UTC": "2026-06-11T12:00:00Z",
        }):
            info = resolve_build_info()
        assert info.git_commit == "abc1234"
        assert info.git_branch == "feat/test"
        assert info.build_time_utc == "2026-06-11T12:00:00Z"

    def test_build_info_no_env_returns_none_git_fields(self):
        env = {
            k: v for k, v in os.environ.items()
            if k not in ("BUILDER_GIT_COMMIT", "BUILDER_GIT_BRANCH", "BUILDER_BUILD_TIME_UTC")
        }
        with patch.dict(os.environ, env, clear=True):
            info = resolve_build_info()
        assert info.git_commit is None
        assert info.git_branch is None
        assert info.build_time_utc is None

    def test_build_info_schema_version_default(self):
        info = resolve_build_info()
        assert info.schema_version == "1.0"

    def test_build_info_name_default(self):
        info = resolve_build_info()
        assert info.name == "nautilus-builder"

    def test_build_info_extra_fields_forbidden(self):
        with pytest.raises(Exception):
            BuilderBuildInfo(
                version="0.1.0",
                unknown_field="bad",
            )
