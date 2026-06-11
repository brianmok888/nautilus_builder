"""Readiness route — GET /api/readiness returns machine-readable readiness matrix."""
from __future__ import annotations


def readiness_payload():
    """Return the current Builder readiness matrix as a dict."""
    from packages.readiness.service import get_readiness_matrix
    return get_readiness_matrix().model_dump()
