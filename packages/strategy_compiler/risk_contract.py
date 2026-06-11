"""Risk contract artifact — deterministic hashable risk parameters."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from packages.strategy_compiler.hashing import canonical_hash


class RiskContractArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    max_spread_bps: float = Field(gt=0)
    max_position_notional: float = Field(gt=0)
    max_daily_loss: float = Field(gt=0)
    max_slippage_bps: float | None = None
    max_impact_bps: float | None = None
    min_top_depth_usd: float | None = None
    cooldown_after_loss: int | None = None

    def compute_hash(self) -> str:
        """Deterministic hash of risk contract parameters."""
        data = self.model_dump(exclude_none=True)
        return canonical_hash(data)
