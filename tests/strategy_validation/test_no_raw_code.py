from __future__ import annotations

from packages.strategy_validation.validators import validate_strategy_spec

from tests.strategy_spec.test_schema_valid import make_valid_spec


def test_eval_reference_is_rejected() -> None:
    payload = make_valid_spec()
    payload["indicators"]["ema_fast"]["input"] = "eval(close)"

    report = validate_strategy_spec(payload)

    assert report.is_valid is False
    assert any("eval" in error for error in report.errors)


def test_import_reference_in_metadata_is_rejected() -> None:
    payload = make_valid_spec()
    payload["provenance"]["notes"] = "import os"

    report = validate_strategy_spec(payload)

    assert report.is_valid is False
    assert any("import" in error for error in report.errors)
