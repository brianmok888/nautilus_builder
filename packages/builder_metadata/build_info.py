"""Build info resolver — assembles BuilderBuildInfo from canonical version + env."""
from __future__ import annotations

import os

from packages.builder_metadata.models import BuilderBuildInfo
from packages.builder_metadata.version import _read_version_from_metadata, _read_version_from_pyproject


def resolve_build_info() -> BuilderBuildInfo:
    """Resolve BuilderBuildInfo from installed metadata, pyproject.toml, and env vars."""
    installed = _read_version_from_metadata()

    if installed is not None:
        version = installed
        source: str = "installed_metadata"
    else:
        version = _read_version_from_pyproject()
        source = "pyproject"

    git_commit = os.environ.get("BUILDER_GIT_COMMIT")
    git_branch = os.environ.get("BUILDER_GIT_BRANCH")
    build_time_utc = os.environ.get("BUILDER_BUILD_TIME_UTC")

    return BuilderBuildInfo(
        version=version,
        git_commit=git_commit,
        git_branch=git_branch,
        build_time_utc=build_time_utc,
        source=source,
    )


def get_build_info() -> BuilderBuildInfo:
    """Public API: resolve BuilderBuildInfo."""
    return resolve_build_info()
