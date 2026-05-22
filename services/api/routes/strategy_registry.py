from __future__ import annotations

from packages.strategy_registry.service import StrategyRegistryService


def list_external_strategy_payloads() -> list[dict[str, object]]:
    service = StrategyRegistryService()
    return [entry.model_dump(mode="json") for entry in service.list_external_strategies()]
