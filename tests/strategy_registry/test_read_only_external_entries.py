from __future__ import annotations

from packages.strategy_registry.models import ExternalStrategyClassification
from packages.strategy_registry.service import StrategyRegistryService


def test_external_entries_are_read_only_by_default() -> None:
    service = StrategyRegistryService()

    entries = service.list_external_strategies()

    daedalus = next(entry for entry in entries if entry.source == "daedalus")
    assert daedalus.read_only is True
    assert daedalus.editable_in_ux is False


def test_unsafe_execution_strategies_are_not_importable() -> None:
    service = StrategyRegistryService()

    entry = service.get_external_strategy("unsafe_executor")

    assert entry.classification == ExternalStrategyClassification.UNSAFE_EXECUTION_STRATEGY
    assert entry.import_allowed is False
