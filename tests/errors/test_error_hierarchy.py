"""Test the Builder typed error hierarchy."""
from __future__ import annotations

from packages.errors import (
    BuilderError,
    BuilderValidationError,
    CredentialSlotError,
    ExecutionLaneError,
    PromotionError,
)


def test_all_errors_inherit_from_builder_error() -> None:
    assert issubclass(BuilderValidationError, BuilderError)
    assert issubclass(CredentialSlotError, BuilderError)
    assert issubclass(ExecutionLaneError, BuilderError)
    assert issubclass(PromotionError, BuilderError)


def test_all_errors_are_exception_subclasses() -> None:
    assert issubclass(BuilderError, Exception)


def test_errors_carry_message() -> None:
    err = BuilderValidationError("spec validation failed")
    assert str(err) == "spec validation failed"


def test_errors_distinguish_by_type() -> None:
    errors = [
        BuilderValidationError("v"),
        CredentialSlotError("c"),
        ExecutionLaneError("e"),
        PromotionError("p"),
    ]
    types = {type(e) for e in errors}
    assert len(types) == 4
