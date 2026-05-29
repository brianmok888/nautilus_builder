from __future__ import annotations

from packages.errors import (
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


def test_all_errors_inherit_from_builder_error() -> None:
    assert issubclass(BuilderValidationError, BuilderError)
    assert issubclass(BuilderNotFoundError, BuilderError)
    assert issubclass(BuilderConflictError, BuilderError)
    assert issubclass(BuilderForbiddenError, BuilderError)
    assert issubclass(CredentialSlotError, BuilderValidationError)
    assert issubclass(ExecutionLaneError, BuilderError)
    assert issubclass(PromotionError, BuilderError)
    assert issubclass(AiBuilderError, BuilderError)


def test_validation_error_is_catchable_as_base() -> None:
    with pytest.raises(BuilderError):
        raise BuilderValidationError("test validation failure")


def test_credential_slot_error_is_catchable_as_validation() -> None:
    with pytest.raises(BuilderValidationError):
        raise CredentialSlotError("bad slot")


import pytest
