from __future__ import annotations

from packages.strategy_validation.validators import validate_strategy_spec

from tests.strategy_spec.test_schema_valid import make_valid_spec


def test_submit_order_reference_is_rejected() -> None:
    payload = make_valid_spec()
    payload["rules"]["long_entry"] = {
        "all": [
            {"gt": ["submit_order", 1]},
        ]
    }

    report = validate_strategy_spec(payload)

    assert report.is_valid is False
    assert any("submit_order" in error for error in report.errors)


def test_trade_action_reference_is_rejected() -> None:
    payload = make_valid_spec()
    payload["rules"]["long_exit"] = {
        "any": [
            {"lt": ["TradeAction", 0]},
        ]
    }

    report = validate_strategy_spec(payload)

    assert report.is_valid is False
    assert any("TradeAction" in error for error in report.errors)


def test_unknown_operator_is_rejected_by_validator_report() -> None:
    payload = make_valid_spec()
    payload["rules"]["long_entry"] = {
        "all": [
            {"future_peek": ["ema_fast", "ema_slow"]},
        ]
    }

    report = validate_strategy_spec(payload)

    assert report.is_valid is False
    assert any("future_peek" in error for error in report.errors)
