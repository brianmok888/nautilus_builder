from __future__ import annotations

from packages.strategy_spec.models import StrategySpec


class InMemoryStrategyRepository:
    def __init__(self) -> None:
        self._records: dict[str, list[StrategySpec]] = {}

    def save(self, spec: StrategySpec) -> dict[str, object]:
        strategy_id = "strategy_001" if not self._records else f"strategy_{len(self._records) + 1:03d}"
        self._records.setdefault(strategy_id, []).append(spec)
        return {"strategy_id": strategy_id, "spec": spec.model_dump(mode="json")}

    def list(self) -> list[dict[str, object]]:
        return [
            {"strategy_id": strategy_id, "latest_spec": versions[-1].model_dump(mode="json")}
            for strategy_id, versions in self._records.items()
        ]

    def detail(self, strategy_id: str) -> dict[str, object] | None:
        versions = self._records.get(strategy_id)
        if not versions:
            return None
        return {
            "strategy_id": strategy_id,
            "versions": [{"spec": version.model_dump(mode="json")} for version in versions],
        }
