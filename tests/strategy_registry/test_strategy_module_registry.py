from __future__ import annotations

import pytest

from packages.strategy_registry import StrategyModuleRegistryService


def test_strategy_module_registry_selects_safe_strategy_spec_module() -> None:
    registry = StrategyModuleRegistryService()

    entry = registry.select_for_strategy_spec("rule_graph_backtest")

    assert entry.module_id == "rule_graph_backtest"
    assert entry.strategy_class_path == "packages.nautilus_rule_graph.strategy:RuleGraphBacktestStrategy"
    assert entry.config_class_path == "packages.nautilus_rule_graph.config:RuleGraphStrategyConfig"
    assert entry.input_kind == "strategy_spec"
    assert entry.read_only is True
    assert entry.execution_authority is False
    assert entry.live_trading_enabled is False
    assert entry.credentials_required is False


def test_strategy_module_registry_rejects_unknown_module_selection() -> None:
    registry = StrategyModuleRegistryService()

    with pytest.raises(ValueError, match="unknown strategy module"):
        registry.select_for_strategy_spec("unknown_python_strategy")


def test_strategy_module_registry_rejects_unallowlisted_module_paths() -> None:
    registry = StrategyModuleRegistryService()

    with pytest.raises(ValueError, match="module path is not allowlisted"):
        registry.register_safe_module(
            module_id="unsafe_os",
            strategy_class_path="os:system",
            config_class_path="packages.nautilus_rule_graph.config:RuleGraphStrategyConfig",
            input_kind="strategy_spec",
        )


def test_strategy_module_registry_does_not_import_or_execute_modules() -> None:
    registry = StrategyModuleRegistryService()

    entry = registry.select_for_strategy_spec("rule_graph_backtest")

    assert entry.resolution_mode == "metadata_only"
