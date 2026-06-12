"""TDD tests for StrategySpec output_mode enforcement (M-04)."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from packages.strategy_spec.models import OutputMode, StrategySpec


def _minimal_spec_dict(**overrides):
    """Return a minimal valid StrategySpec payload."""
    base = dict(
        schema_version="v1",
        version="0.1.0",
        stage="draft",
        status="draft",
        created_from="user",
        adapter_id="binance",
        venue="BINANCE",
        instrument_id="BTCUSDT-PERP.BINANCE",
        bar_type="BTCUSDT-PERP.BINANCE-5-MINUTE-LAST-EXTERNAL",
        data_range={"start": "2024-01-01", "end": "2024-06-01"},
        indicators={"ema": {"type": "EMA", "input": "close", "period": 20}},
        rules={"entry": {"all": [{"gt": ["ema.close", "close"]}]}},
        risk={
            "position_size_pct": 0.1,
            "stop_loss_pct": 0.02,
            "take_profit_pct": 0.04,
            "max_hold_bars": 100,
        },
        validation={
            "bar_close_only": True,
            "no_lookahead_required": True,
            "requires_backtest_before_shadow": True,
            "output_mode": "signal_preview_only",
        },
        provenance={"created_by": "user"},
    )
    base.update(overrides)
    return base


class TestOutputModeEnforcement:
    def test_signal_preview_only_is_accepted(self):
        spec = StrategySpec(**_minimal_spec_dict())
        assert spec.validation.output_mode == OutputMode.SIGNAL_PREVIEW_ONLY

    def test_output_mode_must_be_signal_preview_only(self):
        payload = _minimal_spec_dict()
        payload["validation"]["output_mode"] = "live_execution"
        with pytest.raises(ValidationError, match="output_mode"):
            StrategySpec(**payload)

    def test_output_mode_literal_guard_on_strategy_spec(self):
        payload = _minimal_spec_dict()
        spec = StrategySpec(**payload)
        assert spec.validation.output_mode.value == "signal_preview_only"
