from __future__ import annotations

import pytest
from pydantic import ValidationError

from packages.strategy_spec.models import StrategySpec

from .test_schema_valid import make_valid_spec


def test_unknown_top_level_field_fails() -> None:
    payload = make_valid_spec()
    payload["unexpected"] = "nope"

    with pytest.raises(ValidationError) as exc:
        StrategySpec.model_validate(payload)

    assert exc.value.errors()[0]["type"] == "extra_forbidden"


def test_unknown_indicator_type_fails() -> None:
    payload = make_valid_spec()
    payload["indicators"]["ema_fast"]["type"] = "MAGIC_ALPHA"

    with pytest.raises(ValidationError):
        StrategySpec.model_validate(payload)


def test_unknown_operator_fails() -> None:
    payload = make_valid_spec()
    payload["rules"]["long_entry"] = {
        "all": [
            {"future_peek": ["ema_fast", "ema_slow"]},
        ]
    }

    with pytest.raises(ValidationError):
        StrategySpec.model_validate(payload)


def test_live_execution_direct_mode_fails() -> None:
    payload = make_valid_spec()
    payload["validation"]["output_mode"] = "live_execution_direct"

    with pytest.raises(ValidationError):
        StrategySpec.model_validate(payload)


def test_missing_risk_block_fails() -> None:
    payload = make_valid_spec()
    payload.pop("risk")

    with pytest.raises(ValidationError):
        StrategySpec.model_validate(payload)
