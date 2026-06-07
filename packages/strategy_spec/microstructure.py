"""StrategySpecMicrostructureV1 — microstructure-focused strategy specification.

This schema family supports Nautilus-Daedalus microstructure workflows
with feature references, source health tracking, and advisory-only output.

Safety contract:
- output_mode is always signal_preview_only
- execution_authority is always False
- No executable orders are generated from this spec
"""
from __future__ import annotations

from enum import Enum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


# ---------------------------------------------------------------------------
# Microstructure feature types
# ---------------------------------------------------------------------------

class MicrostructureFeature(str, Enum):
    """Supported microstructure feature references."""
    # Order flow
    OBI = "obi"
    SPREAD_BPS = "spread_bps"
    TOP_DEPTH_USD = "top_depth_usd"
    DEPTH_NEAR_PRICE_USD = "depth_near_price_usd"
    PULL_STACK_SCORE = "pull_stack_score"
    # Volume / flow
    CVD = "cvd"
    CVD_DIVERGENCE = "cvd_divergence"
    ABSORPTION = "absorption"
    AGGRESSIVE_BUY_VOLUME = "aggressive_buy_volume"
    AGGRESSIVE_SELL_VOLUME = "aggressive_sell_volume"
    # Liquidity
    HEATMAP_LIQUIDITY = "heatmap_liquidity"
    LIQUIDITY_WALLS = "liquidity_walls"
    # Volume profile
    SVP_POC = "svp_poc"
    SVP_VAH = "svp_vah"
    SVP_VAL = "svp_val"
    HVN = "hvn"
    LVN = "lvn"
    # Funding / liquidation
    FUNDING_RATE = "funding_rate"
    FUNDING_Z_SCORE = "funding_z_score"
    LIQUIDATION_IMBALANCE = "liquidation_imbalance"
    LIQUIDATION_CLUSTERS = "liquidation_clusters"
    # Reference price
    VWAP_SESSION = "vwap_session"
    ANCHORED_VWAP = "anchored_vwap"
    # Toxicity / resilience
    VPIN_TOXICITY = "vpin_toxicity"
    BOOK_RESILIENCE = "book_resilience"
    LIQUIDITY_REPLENISHMENT = "liquidity_replenishment"


# ---------------------------------------------------------------------------
# Source health
# ---------------------------------------------------------------------------

class SourceHealth(str, Enum):
    """Health status semantics for feature data sources."""
    SOURCE_AVAILABLE = "source_available"
    STALE = "stale"
    MISSING = "missing"
    TRUE_ZERO = "true_zero"
    SYNTHETIC_FALLBACK_USED = "synthetic_fallback_used"


# ---------------------------------------------------------------------------
# Source health record for a single feature
# ---------------------------------------------------------------------------

class FeatureSourceHealth(StrictModel):
    """Source health record for a single microstructure feature."""
    feature: MicrostructureFeature
    source_available: bool
    last_update_ts_ns: int | None = None
    age_ms: int | None = None
    stale: bool = False
    missing: bool = False
    true_zero: bool = False
    synthetic_fallback_used: bool = False
    provenance: str = "unknown"
    source_status: SourceHealth = SourceHealth.SOURCE_AVAILABLE


# ---------------------------------------------------------------------------
# Feature reference in a microstructure spec
# ---------------------------------------------------------------------------

class MicrostructureFeatureRef(StrictModel):
    """A reference to a microstructure feature with required source health."""
    feature: MicrostructureFeature
    required: bool = True
    max_staleness_ms: int | None = None
    fail_closed_on_missing: bool = True
    fallback_value: float | None = None

    @field_validator("max_staleness_ms")
    @classmethod
    def validate_max_staleness(cls, v: int | None) -> int | None:
        if v is not None and v <= 0:
            raise ValueError("max_staleness_ms must be positive if set")
        return v


# ---------------------------------------------------------------------------
# Signal rule for microstructure spec
# ---------------------------------------------------------------------------

class MicrostructureSignalRule(StrictModel):
    """A signal rule combining microstructure feature references."""
    name: str = Field(min_length=1, max_length=128)
    features: list[MicrostructureFeatureRef] = Field(min_length=1)
    condition: str = Field(min_length=1)
    direction: Literal["long", "short", "neutral"] = "long"
    confidence_threshold: float = Field(ge=0.0, le=1.0, default=0.5)

    @field_validator("condition")
    @classmethod
    def validate_condition_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("condition must not be empty")
        return v


# ---------------------------------------------------------------------------
# Risk block for microstructure spec
# ---------------------------------------------------------------------------

class MicrostructureRiskBlock(StrictModel):
    """Risk parameters for microstructure strategy."""
    max_position_notional_usd: Annotated[float, Field(gt=0)]
    max_loss_notional_usd: Annotated[float, Field(gt=0)]
    max_hold_ms: Annotated[int, Field(gt=0)]
    min_signal_confidence: Annotated[float, Field(ge=0.0, le=1.0)] = 0.5


# ---------------------------------------------------------------------------
# The full StrategySpecMicrostructureV1
# ---------------------------------------------------------------------------

class StrategySpecMicrostructureV1(StrictModel):
    """Microstructure strategy specification for Nautilus-Daedalus.

    This spec compiles only to preview/evidence artifacts.
    It must not generate executable orders.

    Safety contract:
    - output_mode is always signal_preview_only
    - execution_authority is always False
    """
    schema_version: Literal["microstructure_v1"] = "microstructure_v1"
    version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    adapter_id: str = Field(min_length=1)
    venue: str = Field(min_length=1)
    instrument_id: str = Field(min_length=1)
    features: list[MicrostructureFeatureRef] = Field(min_length=1)
    signals: list[MicrostructureSignalRule] = Field(min_length=1)
    risk: MicrostructureRiskBlock
    output_mode: Literal["signal_preview_only"] = "signal_preview_only"
    execution_authority: Literal[False] = False

    @model_validator(mode="after")
    def validate_no_execution_authority(self) -> "StrategySpecMicrostructureV1":
        if self.execution_authority is not False:
            raise ValueError("Microstructure spec must have execution_authority=False")
        if self.output_mode != "signal_preview_only":
            raise ValueError("Microstructure spec must have output_mode=signal_preview_only")
        return self

    def get_required_features(self) -> list[MicrostructureFeatureRef]:
        """Return features marked as required."""
        return [f for f in self.features if f.required]

    def get_optional_features(self) -> list[MicrostructureFeatureRef]:
        """Return features not marked as required."""
        return [f for f in self.features if not f.required]

    def validate_source_health(
        self, health_records: list[FeatureSourceHealth]
    ) -> list[str]:
        """Validate source health for all required features.

        Returns list of violations (empty if all healthy).
        """
        health_map = {h.feature: h for h in health_records}
        violations: list[str] = []

        for ref in self.get_required_features():
            if ref.feature not in health_map:
                if ref.fail_closed_on_missing:
                    violations.append(
                        f"Required feature {ref.feature.value} has no health record"
                    )
                continue

            health = health_map[ref.feature]

            if health.missing and ref.fail_closed_on_missing:
                violations.append(
                    f"Required feature {ref.feature.value} is missing"
                )

            if health.stale:
                if ref.max_staleness_ms is not None:
                    if health.age_ms is not None and health.age_ms > ref.max_staleness_ms:
                        violations.append(
                            f"Required feature {ref.feature.value} is stale "
                            f"(age={health.age_ms}ms > max={ref.max_staleness_ms}ms)"
                        )
                else:
                    violations.append(
                        f"Required feature {ref.feature.value} is stale (no max_staleness_ms configured)"
                    )

            if health.synthetic_fallback_used and ref.fail_closed_on_missing:
                violations.append(
                    f"Required feature {ref.feature.value} is using synthetic fallback"
                )

        return violations


# ---------------------------------------------------------------------------
# Type alias for backward compat: existing StrategySpec is "classic"
# ---------------------------------------------------------------------------

from .models import StrategySpec as StrategySpecClassicV1

__all__ = [
    "FeatureSourceHealth",
    "MicrostructureFeature",
    "MicrostructureFeatureRef",
    "MicrostructureRiskBlock",
    "MicrostructureSignalRule",
    "SourceHealth",
    "StrategySpecClassicV1",
    "StrategySpecMicrostructureV1",
]
