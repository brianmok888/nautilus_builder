from __future__ import annotations

from packages.strategy_compiler.compiler import compile_strategy_spec

from tests.strategy_spec.test_schema_valid import make_valid_spec


def test_compile_hash_is_stable_for_same_spec() -> None:
    payload = make_valid_spec()

    first = compile_strategy_spec(payload, profile="backtest")
    second = compile_strategy_spec(payload, profile="backtest")

    assert first.compile_hash == second.compile_hash
