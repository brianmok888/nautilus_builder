"""BuilderBuildInfo model — canonical build metadata for nautilus_builder."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class BuilderBuildInfo(BaseModel):
    """Canonical build metadata returned by /health/build and embedded in evidence."""

    model_config = ConfigDict(extra="forbid")

    name: str = "nautilus-builder"
    version: str
    git_commit: str | None = None
    git_branch: str | None = None
    build_time_utc: str | None = None
    schema_version: str = "1.0"
    source: Literal["installed_metadata", "pyproject", "env", "unknown"] = "unknown"
