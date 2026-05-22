from __future__ import annotations

from packages.strategy_compiler.compiler import compile_strategy_spec

from tests.strategy_spec.test_schema_valid import make_valid_spec


def test_valid_spec_compiles_to_backtest_artifact() -> None:
    artifact = compile_strategy_spec(make_valid_spec(), profile="backtest")

    assert artifact.profile == "backtest"
    assert artifact.strategy_class == "RuleGraphBacktestStrategy"
    assert artifact.output_mode == "backtest_order_intent"
    assert artifact.spec_version == "0.1.0-draft.1"
    assert artifact.adapter_id == "BINANCE_PERP"
    assert artifact.instrument_id == "BTCUSDT-PERP"
    assert artifact.compile_hash
