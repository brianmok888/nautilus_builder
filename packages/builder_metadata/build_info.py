"""Build info helpers for /health/build and operator display."""
from __future__ import annotations

import os

from packages.builder_metadata.version import get_canonical_version


def get_build_info() -> dict[str, str]:
    """Return build metadata dict for health endpoints."""
    return {
        "version": get_canonical_version(),
        "commit": os.environ.get("GIT_COMMIT_SHA", "dev"),
        "build_time": os.environ.get("BUILD_TIME", "unknown"),
    }
