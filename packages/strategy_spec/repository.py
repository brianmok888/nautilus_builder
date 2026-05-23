from __future__ import annotations

from packages.strategy_spec.models import StrategySpec


class InMemoryStrategyRepository:
    def __init__(self) -> None:
        self._records: dict[str, list[StrategySpec]] = {}

    @staticmethod
    def _lineage_id(strategy_id: str) -> str:
        return f"lineage_{strategy_id}"

    @staticmethod
    def _version_id(strategy_id: str, index: int) -> str:
        return f"{strategy_id}_v{index:03d}"

    def save(self, spec: StrategySpec) -> dict[str, object]:
        strategy_id = "strategy_001" if not self._records else f"strategy_{len(self._records) + 1:03d}"
        self._records.setdefault(strategy_id, []).append(spec)
        return {
            "strategy_id": strategy_id,
            "strategy_lineage_id": self._lineage_id(strategy_id),
            "strategy_version_id": self._version_id(strategy_id, 1),
            "spec": spec.model_dump(mode="json"),
        }

    def update_draft(self, strategy_id: str, spec: StrategySpec) -> dict[str, object] | None:
        versions = self._records.get(strategy_id)
        if versions is None:
            return None
        if not versions:
            versions.append(spec)
        else:
            versions[-1] = spec
        return {
            "strategy_id": strategy_id,
            "strategy_lineage_id": self._lineage_id(strategy_id),
            "strategy_version_id": self._version_id(strategy_id, len(versions)),
            "spec": spec.model_dump(mode="json"),
        }

    def create_version(self, strategy_id: str, spec: StrategySpec) -> dict[str, object] | None:
        versions = self._records.get(strategy_id)
        if versions is None:
            return None
        versions.append(spec)
        return {
            "strategy_id": strategy_id,
            "strategy_lineage_id": self._lineage_id(strategy_id),
            "strategy_version_id": self._version_id(strategy_id, len(versions)),
            "spec": spec.model_dump(mode="json"),
        }

    def list(self) -> list[dict[str, object]]:
        return [
            {
                "strategy_id": strategy_id,
                "strategy_lineage_id": self._lineage_id(strategy_id),
                "strategy_version_id": self._version_id(strategy_id, len(versions)),
                "latest_spec": versions[-1].model_dump(mode="json"),
            }
            for strategy_id, versions in self._records.items()
        ]

    def detail(self, strategy_id: str) -> dict[str, object] | None:
        versions = self._records.get(strategy_id)
        if not versions:
            return None
        return {
            "strategy_id": strategy_id,
            "strategy_lineage_id": self._lineage_id(strategy_id),
            "versions": [
                {"strategy_version_id": self._version_id(strategy_id, index), "spec": version.model_dump(mode="json")}
                for index, version in enumerate(versions, start=1)
            ],
        }
