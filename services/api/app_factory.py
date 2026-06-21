"""App factory — creates a configured FastAPI application.

This is the canonical factory for creating Builder API instances.
The existing fastapi_app.py delegates to this for compatibility.
"""
from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from fastapi import FastAPI



@runtime_checkable
class RateLimiterProtocol(Protocol):
    def is_allowed(self, key: str) -> bool: ...


def create_app(
    *,
    artifact_store: Any = None,
    rate_limiter: RateLimiterProtocol | None = None,
) -> "FastAPI":
    """Create a configured FastAPI application using the canonical factory.

    This is a thin wrapper that delegates to the existing create_fastapi_app
    to maintain backward compatibility while introducing the factory pattern.
    """
    from services.api.fastapi_app import create_fastapi_app

    return create_fastapi_app(
        artifact_store=artifact_store,
        rate_limiter=rate_limiter,
    )
