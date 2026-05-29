"""Typed error hierarchy for Nautilus Builder services."""
from __future__ import annotations


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
