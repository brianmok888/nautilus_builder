"""Typed error hierarchy for Nautilus Builder services."""
from __future__ import annotations

from .errors import (
    AiBuilderError,
    BuilderConflictError,
    BuilderError,
    BuilderForbiddenError,
    BuilderNotFoundError,
    BuilderValidationError,
    CredentialSlotError,
    ExecutionLaneError,
    PromotionError,
)


__all__ = [
    "AiBuilderError",
    "BuilderConflictError",
    "BuilderError",
    "BuilderForbiddenError",
    "BuilderNotFoundError",
    "BuilderValidationError",
    "CredentialSlotError",
    "ExecutionLaneError",
    "PromotionError",
]
