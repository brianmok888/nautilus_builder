"""Typed error hierarchy for Nautilus Builder services."""
from __future__ import annotations

from enum import Enum as _Enum
from typing import Any as _Any


class BuilderError(Exception):
    """Base error for all Builder service failures."""


class BuilderValidationError(BuilderError):
    """Raised when strategy spec validation or lifecycle checks fail."""


class BuilderNotFoundError(BuilderError):
    """Raised when a requested resource is not found."""


class BuilderConflictError(BuilderError):
    """Raised when a write conflicts with existing state."""


class BuilderForbiddenError(BuilderError):
    """Raised when the caller lacks permission for the action."""


class CredentialSlotError(BuilderValidationError):
    """Raised when credential slot operations fail (missing, invalid, permission)."""


class ExecutionLaneError(BuilderError):
    """Raised when execution lane session operations fail."""


class PromotionError(BuilderError):
    """Raised when promotion contract validation or gate checks fail."""


class AiBuilderError(BuilderError):
    """Raised when AI builder draft or apply operations fail."""


# --- Structured API error model ---



class ErrorCode(str, _Enum):
    """Stable error codes for structured API responses."""
    AUTH_REQUIRED = "AUTH_REQUIRED"
    AUTH_INVALID = "AUTH_INVALID"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    IDEMPOTENCY_CONFLICT = "IDEMPOTENCY_CONFLICT"
    RATE_LIMITED = "RATE_LIMITED"
    ARTIFACT_NOT_FOUND = "ARTIFACT_NOT_FOUND"
    REPLAY_FAILED = "REPLAY_FAILED"
    PROMOTION_BLOCKED = "PROMOTION_BLOCKED"
    PRODUCTION_CONFIG_INVALID = "PRODUCTION_CONFIG_INVALID"
    NOT_FOUND = "NOT_FOUND"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class StructuredError(Exception):
    """Structured error with code, message, request_id, and optional details."""

    def __init__(
        self,
        code: ErrorCode,
        message: str,
        request_id: str | None = None,
        details: list[dict[str, _Any]] | None = None,
    ) -> None:
        self.code = code
        self.message = message
        self.request_id = request_id
        self.details = details
        super().__init__(message)


def error_response(
    *,
    code: ErrorCode,
    message: str,
    request_id: str | None = None,
    details: list[dict[str, _Any]] | None = None,
) -> dict[str, _Any]:
    """Build a structured error response dict suitable for JSON API responses."""
    error: dict[str, _Any] = {
        "code": code.value,
        "message": message,
    }
    if request_id is not None:
        error["request_id"] = request_id
    result: dict[str, _Any] = {"error": error}
    if details is not None:
        result["error"]["details"] = details
    return result
