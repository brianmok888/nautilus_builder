"""FastAPI dependency injection — shared dependencies for route modules."""
from __future__ import annotations

from typing import Any, Callable

from fastapi import Header

from packages.auth.context_middleware import UserProjectContext, require_context


def get_context(authorization: str | None = Header(default=None)) -> tuple[UserProjectContext | None, dict[str, Any] | None]:
    """Standard dependency for routes that need project-scoped auth context."""
    return require_context(authorization)
