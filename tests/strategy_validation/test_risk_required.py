from __future__ import annotations

from packages.strategy_validation.validators import validate_strategy_spec

from tests.strategy_spec.test_schema_valid import make_valid_spec


def test_missing_risk_block_fails_validation() -> None:
    payload = make_valid_spec()
    payload.pop("risk")

    report = validate_strategy_spec(payload)

    assert report.is_valid is False
    assert any("risk" in error.lower() for error in report.errors)


def test_bar_close_only_must_be_true() -> None:
    payload = make_valid_spec()
    payload["validation"]["bar_close_only"] = False

    report = validate_strategy_spec(payload)

    assert report.is_valid is False
    assert any("bar_close_only" in error for error in report.errors)


def test_no_lookahead_required_must_be_true() -> None:
    payload = make_valid_spec()
    payload["validation"]["no_lookahead_required"] = False

    report = validate_strategy_spec(payload)

    assert report.is_valid is False
    assert any("no_lookahead_required" in error for error in report.errors)
