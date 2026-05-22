from __future__ import annotations

from packages.strategy_compiler.compiler import compile_strategy_spec

from tests.strategy_spec.test_schema_valid import make_valid_spec


def test_live_profile_emits_signal_preview_only() -> None:
    artifact = compile_strategy_spec(make_valid_spec(), profile="signal_preview_only")

    assert artifact.profile == "signal_preview_only"
    assert artifact.strategy_class == "RuleGraphSignalStrategy"
    assert artifact.output_mode == "signal_preview_only"
    assert artifact.execution_authority is False
