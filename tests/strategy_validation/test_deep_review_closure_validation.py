from __future__ import annotations

from tests.strategy_spec.test_schema_valid import make_valid_spec
from packages.strategy_validation.validators import validate_strategy_spec


def test_requires_backtest_before_shadow_must_be_true() -> None:
    spec = make_valid_spec()
    spec["validation"]["requires_backtest_before_shadow"] = False

    report = validate_strategy_spec(spec)

    assert report.is_valid is False
    assert "requires_backtest_before_shadow must be true" in report.errors


def test_data_range_must_parse_and_start_before_end() -> None:
    spec = make_valid_spec()
    spec["data_range"] = {
        "start": "2025-06-01T00:00:00Z",
        "end": "2025-01-01T00:00:00Z",
    }

    report = validate_strategy_spec(spec)

    assert report.is_valid is False
    assert "data_range.start must be before data_range.end" in report.errors


def test_data_range_rejects_invalid_datetime_strings() -> None:
    spec = make_valid_spec()
    spec["data_range"]["start"] = "tomorrow-ish"

    report = validate_strategy_spec(spec)

    assert report.is_valid is False
    assert "data_range.start must be an ISO-8601 datetime" in report.errors


def test_rule_operators_require_exactly_two_operands() -> None:
    spec = make_valid_spec()
    spec["rules"]["long_entry"] = {"all": [{"gt": ["rsi"]}, {"lt": ["rsi", 40, "extra"]}]}

    report = validate_strategy_spec(spec)

    assert report.is_valid is False
    assert "rules.long_entry.all[0].gt must define exactly 2 operands" in report.errors
    assert "rules.long_entry.all[1].lt must define exactly 2 operands" in report.errors


def test_rule_operands_must_reference_known_indicators_or_fields() -> None:
    spec = make_valid_spec()
    spec["rules"]["long_entry"] = {"all": [{"gt": ["unknown_indicator", 52]}]}

    report = validate_strategy_spec(spec)

    assert report.is_valid is False
    assert "rules.long_entry.all[0].gt operand unknown_indicator is not a known indicator or field" in report.errors


def test_imported_provenance_enum_is_not_rejected_as_raw_code() -> None:
    spec = make_valid_spec()
    spec["created_from"] = "imported"
    spec["provenance"]["created_by"] = "imported"

    report = validate_strategy_spec(spec)

    assert report.is_valid is True
    assert not any("raw code pattern detected: import" == error for error in report.errors)


def test_raw_import_statement_is_still_rejected() -> None:
    spec = make_valid_spec()
    spec["rules"]["long_entry"] = {"all": [{"gt": ["import os", 1]}]}

    report = validate_strategy_spec(spec)

    assert report.is_valid is False
    assert "raw code pattern detected: import" in report.errors
