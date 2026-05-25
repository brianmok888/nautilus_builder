from __future__ import annotations

from pathlib import Path

from packages.strategy_spec.models import StrategySpec

from .test_schema_valid import make_valid_spec


def test_documented_indicator_types_are_executable_schema_truth() -> None:
    payload = make_valid_spec()
    payload["indicators"] = {
        "ema": {"type": "EMA", "input": "close", "period": 20},
        "sma": {"type": "SMA", "input": "close", "period": 20},
        "rsi": {"type": "RSI", "input": "close", "period": 14},
        "macd": {"type": "MACD", "input": "close", "period": 12},
        "atr": {"type": "ATR", "input": "close", "period": 14},
        "bb": {"type": "BollingerBands", "input": "close", "period": 20},
        "vwap": {"type": "VWAP", "input": "close", "period": 20},
    }

    spec = StrategySpec.model_validate(payload)

    assert set(spec.indicators) == {"ema", "sma", "rsi", "macd", "atr", "bb", "vwap"}


def test_documented_comparison_operators_are_executable_schema_truth() -> None:
    payload = make_valid_spec()
    payload["rules"] = {
        "entry": {
            "all": [
                {"crossed_above": ["ema_fast", "ema_slow"]},
                {"crossed_below": ["ema_fast", "ema_slow"]},
                {"gt": ["rsi", 52]},
                {"lt": ["rsi", 45]},
                {"gte": ["rsi", 50]},
                {"lte": ["rsi", 70]},
                {"eq": ["regime", "risk_on"]},
            ]
        }
    }

    spec = StrategySpec.model_validate(payload)

    assert len(spec.rules["entry"].all or []) == 7


def test_hardguard_docs_name_executable_combinators_instead_of_direct_logical_operators() -> None:
    docs = Path("doc/nautilus_builder_hardguards.md").read_text()

    assert "Executable combinators:" in docs
    assert "all" in docs
    assert "any" in docs
    assert "not is not part of the executable MVP schema" in docs
