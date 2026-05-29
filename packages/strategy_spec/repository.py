from __future__ import annotations

from packages.auth import ProjectScopeError, UserProjectContext
from packages.strategy_spec.models import StrategySpec


class InMemoryStrategyRepository:
    def __init__(self) -> None:
        self._records: dict[str, list[StrategySpec]] = {}
        self._scopes: dict[str, UserProjectContext] = {}

    @staticmethod
    def _lineage_id(strategy_id: str) -> str:
        return f"lineage_{strategy_id}"

    @staticmethod
    def _version_id(strategy_id: str, index: int) -> str:
        return f"{strategy_id}_v{index:03d}"

    def save(self, spec: StrategySpec, *, context: UserProjectContext | None = None) -> dict[str, object]:
        strategy_id = "strategy_001" if not self._records else f"strategy_{len(self._records) + 1:03d}"
        self._records.setdefault(strategy_id, []).append(spec)
        if context is not None:
            self._scopes[strategy_id] = context
        return self._record(strategy_id, spec, 1)

    def save_explicit(self, strategy_id: str, spec: StrategySpec, *, context: UserProjectContext | None = None) -> dict[str, object]:
        self._records.setdefault(strategy_id, []).append(spec)
        if context is not None:
            self._scopes[strategy_id] = context
        return self._record(strategy_id, spec, len(self._records[strategy_id]))

    def update_draft(
        self,
        strategy_id: str,
        spec: StrategySpec,
        *,
        context: UserProjectContext | None = None,
    ) -> dict[str, object] | None:
        versions = self._records.get(strategy_id)
        if versions is None:
            return None
        self._assert_scope(strategy_id, context)
        if not versions:
            versions.append(spec)
        else:
            versions[-1] = spec
        return self._record(strategy_id, spec, len(versions))

    def create_version(
        self,
        strategy_id: str,
        spec: StrategySpec,
        *,
        context: UserProjectContext | None = None,
    ) -> dict[str, object] | None:
        versions = self._records.get(strategy_id)
        if versions is None:
            return None
        self._assert_scope(strategy_id, context)
        versions.append(spec)
        return self._record(strategy_id, spec, len(versions))

    def spec_for_version(
        self,
        strategy_version_id: str,
        *,
        context: UserProjectContext | None = None,
    ) -> StrategySpec | None:
        for strategy_id, versions in self._records.items():
            if not self._scope_matches(strategy_id, context):
                continue
            for index, spec in enumerate(versions, start=1):
                if self._version_id(strategy_id, index) == strategy_version_id:
                    return spec
        return None

    def list(self, *, context: UserProjectContext | None = None) -> list[dict[str, object]]:
        return [
            {
                "strategy_id": strategy_id,
                "strategy_lineage_id": self._lineage_id(strategy_id),
                "strategy_version_id": self._version_id(strategy_id, len(versions)),
                "status": versions[-1].status.value,
                "latest_spec": versions[-1].model_dump(mode="json"),
                **self._scope_payload(strategy_id),
            }
            for strategy_id, versions in self._records.items()
            if self._scope_matches(strategy_id, context)
        ]

    def detail(self, strategy_id: str, *, context: UserProjectContext | None = None) -> dict[str, object] | None:
        versions = self._records.get(strategy_id)
        if not versions:
            return None
        self._assert_scope(strategy_id, context)
        return {
            "strategy_id": strategy_id,
            "strategy_lineage_id": self._lineage_id(strategy_id),
            "status": versions[-1].status.value,
            "versions": [
                {"strategy_version_id": self._version_id(strategy_id, index), "spec": version.model_dump(mode="json")}
                for index, version in enumerate(versions, start=1)
            ],
            **self._scope_payload(strategy_id),
        }

    def _record(self, strategy_id: str, spec: StrategySpec, version_index: int) -> dict[str, object]:
        return {
            "strategy_id": strategy_id,
            "strategy_lineage_id": self._lineage_id(strategy_id),
            "strategy_version_id": self._version_id(strategy_id, version_index),
            "status": spec.status.value,
            "spec": spec.model_dump(mode="json"),
            **self._scope_payload(strategy_id),
        }

    def _scope_payload(self, strategy_id: str) -> dict[str, str]:
        scope = self._scopes.get(strategy_id)
        if scope is None:
            return {}
        return {"user_id": scope.user_id, "project_id": scope.project_id}

    def _scope_matches(self, strategy_id: str, context: UserProjectContext | None) -> bool:
        if context is None:
            return True
        scope = self._scopes.get(strategy_id)
        return scope is not None and scope.user_id == context.user_id and scope.project_id == context.project_id

    def _assert_scope(self, strategy_id: str, context: UserProjectContext | None) -> None:
        if context is None:
            return
        if not self._scope_matches(strategy_id, context):
            raise ProjectScopeError(f"strategy {strategy_id} is outside user/project scope")
