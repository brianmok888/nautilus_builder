from __future__ import annotations

import json
from pathlib import Path

import yaml

from packages.strategy_spec.models import StrategySpec
from packages.strategy_spec.schema import export_strategy_spec_schema


def make_valid_spec() -> dict:
    return {
        "schema_version": "1.0.0",
        "version": "0.1.0-draft.1",
        "stage": "draft",
        "status": "draft",
        "created_from": "user",
        "is_frozen": False,
        "adapter_id": "BINANCE_PERP",
        "venue": "BINANCE",
        "instrument_id": "BTCUSDT-PERP",
        "bar_type": "BTCUSDT-PERP.BINANCE-5-MINUTE-LAST-EXTERNAL",
        "data_range": {
            "start": "2025-01-01T00:00:00Z",
            "end": "2025-06-01T00:00:00Z",
        },
        "indicators": {
            "ema_fast": {"type": "EMA", "input": "close", "period": 20},
            "ema_slow": {"type": "EMA", "input": "close", "period": 50},
            "rsi": {"type": "RSI", "input": "close", "period": 14},
        },
        "rules": {
            "long_entry": {
                "all": [
                    {"crossed_above": ["ema_fast", "ema_slow"]},
                    {"gt": ["rsi", 52]},
                ]
            },
            "long_exit": {
                "any": [
                    {"crossed_below": ["ema_fast", "ema_slow"]},
                    {"lt": ["rsi", 45]},
                ]
            },
        },
        "risk": {
            "position_size_pct": 0.05,
            "stop_loss_pct": 0.012,
            "take_profit_pct": 0.024,
            "max_hold_bars": 48,
        },
        "validation": {
            "bar_close_only": True,
            "no_lookahead_required": True,
            "requires_backtest_before_shadow": True,
            "output_mode": "signal_preview_only",
        },
        "provenance": {
            "created_by": "user",
            "parent_version_id": None,
        },
    }


def test_valid_ema_rsi_spec_passes() -> None:
    spec = StrategySpec.model_validate(make_valid_spec())

    assert spec.schema_version == "1.0.0"
    assert spec.stage == "draft"
    assert spec.validation.no_lookahead_required is True
    assert spec.risk.position_size_pct == 0.05


def test_json_schema_export_writes_expected_artifact(tmp_path: Path) -> None:
    output_path = tmp_path / "strategy_spec.schema.json"

    export_strategy_spec_schema(output_path)

    assert output_path.exists()
    schema = json.loads(output_path.read_text())
    assert schema["title"] == "StrategySpec"
    assert "schema_version" in schema["properties"]
    assert "$defs" in schema


def test_example_yaml_loads_as_valid_strategy_spec() -> None:
    example_path = Path("packages/strategy_spec/examples/ema_rsi_pullback.yaml")

    data = yaml.safe_load(example_path.read_text())
    spec = StrategySpec.model_validate(data)

    assert spec.indicators["ema_fast"].type == "EMA"
    assert spec.validation.output_mode == "signal_preview_only"
