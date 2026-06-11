"""Feature dependency graph — maps required features for a compiled strategy."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from packages.strategy_compiler.hashing import canonical_hash


class FeatureNode(BaseModel):
    model_config = ConfigDict(extra="forbid")

    group: str
    name: str
    required: bool = True
    max_staleness_ms: int | None = None
    fail_closed_on_missing: bool = True


class FeatureDependencyGraph(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nodes: list[FeatureNode] = Field(default_factory=list)

    def compute_hash(self) -> str:
        """Deterministic hash of the feature dependency graph."""
        data = [{"group": n.group, "name": n.name, "required": n.required} for n in self.nodes]
        return canonical_hash(data)


def build_feature_dependency_graph(
    feature_inputs: list,
) -> FeatureDependencyGraph:
    """Build a feature dependency graph from StrategySpec v2 feature inputs."""
    nodes = [
        FeatureNode(
            group=fi.group.value if hasattr(fi.group, "value") else str(fi.group),
            name=fi.name,
            required=fi.required,
            max_staleness_ms=fi.max_staleness_ms,
            fail_closed_on_missing=fi.fail_closed_on_missing,
        )
        for fi in feature_inputs
    ]
    return FeatureDependencyGraph(nodes=nodes)
