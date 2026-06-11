"""Standardized API error response model."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class ApiError(BaseModel):
    """Consistent error response shape for all API endpoints."""
    model_config = ConfigDict(extra="forbid")

    error_code: str
    message: str
    request_id: str | None = None
    details: dict[str, Any] = {}
