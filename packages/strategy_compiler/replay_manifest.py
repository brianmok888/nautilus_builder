"""Replay manifest template — deterministic template for backtest replay."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from packages.strategy_compiler.hashing import canonical_hash


class ReplayManifestTemplate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    strategy_artifact_hash: str = Field(min_length=1)
    dataset_manifest_refs: list[str] = Field(default_factory=list)
    warmup_bars: int = Field(gt=0, default=100)
    source_health_policy: str = "fail_closed_on_missing"
    alignment_policy: str = "strict_monotonic"

    def compute_hash(self) -> str:
        """Deterministic hash of replay manifest template."""
        data = self.model_dump()
        return canonical_hash(data)
