from __future__ import annotations

"""Typed error hierarchy for Nautilus Builder services.

All service-layer errors inherit from BuilderError so API routes can
catch uniformly and map to appropriate HTTP status codes.
"""


class BuilderError(Exception):
    """Base error for all Builder service operations."""


class BuilderValidationError(BuilderError):
    """Input or schema validation failed."""


class BuilderNotFoundError(BuilderError):
    """Requested resource was not found."""


class BuilderConflictError(BuilderError):
    """Operation conflicts with existing state."""


class BuilderForbiddenError(BuilderError):
    """Operation not permitted for the current context."""


class CredentialSlotError(BuilderValidationError):
    """Credential slot validation or resolution failed."""


class ExecutionLaneError(BuilderError):
    """Execution lane operation failed."""


class PromotionError(BuilderError):
    """Promotion validation or processing failed."""


class AiBuilderError(BuilderError):
    """AI draft generation or processing failed."""
