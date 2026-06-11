"""StrategySpec v2 — comprehensive ND microstructure strategy specification.

This module extends the strategy specification to fully support Nautilus-Daedalus
microstructure strategies with structured feature inputs, condition DSL, event
detectors, archetypes, overlays, risk contracts, and evidence requirements.

Safety contract:
- execution_authority is always False
- No live order authority is introduced
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Annotated, Literal, Union

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


# ---------------------------------------------------------------------------
# Schema version
# ---------------------------------------------------------------------------

class SchemaVersion(str, Enum):
    V1 = "v1"
    V2 = "v2"


class MarketType(str, Enum):
    SPOT = "spot"
    PERPETUAL = "perpetual"
    FUTURES = "futures"
    OPTIONS = "options"


# ---------------------------------------------------------------------------
# Metadata
# ---------------------------------------------------------------------------

class StrategySpecV2Metadata(StrictModel):
    strategy_id: str = Field(min_length=1)
    lineage_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    schema_version: SchemaVersion = SchemaVersion.V2
    created_by: str = Field(min_length=1)
    created_at: datetime | None = None
    source: str = "user"


# ---------------------------------------------------------------------------
# Universe
# ---------------------------------------------------------------------------

class StrategySpecV2Universe(StrictModel):
    venue: str = Field(min_length=1)
    instrument_id: str = Field(min_length=1)
    timeframe: str = Field(min_length=1)
    asset_class: str | None = None
    market_type: MarketType | None = None
    adapter_profile_id: str | None = None
    dataset_requirements: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Feature inputs — structured group/name pairs
# ---------------------------------------------------------------------------

class FeatureGroup(str, Enum):
    ORDERBOOK = "orderbook"
    TRADES = "trades"
    LIQUIDATION = "liquidation"
    FUNDING = "funding"
    SVP = "svp"
    VWAP = "vwap"
    SOURCE_HEALTH = "source_health"


class FeatureInput(StrictModel):
    group: FeatureGroup
    name: str = Field(min_length=1)
    required: bool = True
    max_staleness_ms: int | None = None
    fail_closed_on_missing: bool = True
    fallback_value: float | None = None


class SourceHealthRequirement(StrictModel):
    feature_group: FeatureGroup
    require_available: bool = True
    max_age_ms: int | None = None
    reject_synthetic_fallback: bool = True
    reject_missing: bool = True


# ---------------------------------------------------------------------------
# Condition DSL
# ---------------------------------------------------------------------------

class ConditionPrimitive(str, Enum):
    COMPARE = "compare"
    BETWEEN = "between"
    CROSS_ABOVE = "cross_above"
    CROSS_BELOW = "cross_below"
    RATE_OF_CHANGE = "rate_of_change"
    PERSISTENCE = "persistence"
    ALL_OF = "all_of"
    ANY_OF = "any_of"
    NOT = "not"
    STALE_BLOCK = "stale_block"
    MISSING_BLOCK = "missing_block"


class ConditionDSL(StrictModel):
    """A condition in the DSL. Operands can be strings (feature names, operators)
    or nested ConditionDSL objects for composites."""
    primitive: ConditionPrimitive
    operands: list[Union[str, float, int, 'ConditionDSL']] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Event detectors — named references without embedding live runtime logic
# ---------------------------------------------------------------------------

class EventDetectorName(str, Enum):
    ABSORPTION_DETECTED = "absorption_detected"
    CVD_DIVERGENCE_DETECTED = "cvd_divergence_detected"
    LIQUIDITY_VACUUM_DETECTED = "liquidity_vacuum_detected"
    EXHAUSTION_DETECTED = "exhaustion_detected"
    PULL_STACK_DETECTED = "pull_stack_detected"
    BOOK_RESILIENCE_RETEST_DETECTED = "book_resilience_retest_detected"
    LIQUIDITY_REPLENISHMENT_DETECTED = "liquidity_replenishment_detected"
    LIQUIDATION_CASCADE_DETECTED = "liquidation_cascade_detected"
    VWAP_RECLAIM_DETECTED = "vwap_reclaim_detected"
    VWAP_REJECTION_DETECTED = "vwap_rejection_detected"


class EventDetector(StrictModel):
    name: str = Field(min_length=1)
    required_features: list[str] = Field(default_factory=list)
    confidence_threshold: float = Field(ge=0.0, le=1.0, default=0.5)


# ---------------------------------------------------------------------------
# Archetypes — strict ND archetypes
# ---------------------------------------------------------------------------

class ArchetypeName(str, Enum):
    ABSORPTION_REVERSAL = "absorption_reversal"
    LIQUIDITY_VACUUM_BREAKOUT = "liquidity_vacuum_breakout"
    EXHAUSTION_FADE = "exhaustion_fade"


class Archetype(StrictModel):
    name: str = Field(min_length=1)
    required_features: list[str] = Field(default_factory=list)
    required_detectors: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Overlays — evidence/filter only, not new authority lanes
# ---------------------------------------------------------------------------

class OverlayName(str, Enum):
    VPIN_TOXICITY_OVERLAY = "vpin_toxicity_overlay"
    VWAP_VALUE_REVERSION = "vwap_value_reversion"
    VWAP_PULLBACK_CONTINUATION = "vwap_pullback_continuation"
    VWAP_RECLAIM_REVERSAL = "vwap_reclaim_reversal"
    VWAP_REJECTION_CONTINUATION = "vwap_rejection_continuation"
    VWAP_COMPRESSION_BREAKOUT = "vwap_compression_breakout"
    BOOK_RESILIENCE_RETEST = "book_resilience_retest"
    LIQUIDITY_REPLENISHMENT_REVERSAL = "liquidity_replenishment_reversal"
    LIQUIDATION_CASCADE_CONTINUATION = "liquidation_cascade_continuation"
    ADVANCED_FOOTPRINT_IMBALANCE = "advanced_footprint_imbalance"


class Overlay(StrictModel):
    name: str = Field(min_length=1)
    role: Literal["evidence", "filter"] = "filter"
    required_features: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Risk contract v2
# ---------------------------------------------------------------------------

class RiskContractV2(StrictModel):
    max_spread_bps: float = Field(gt=0)
    max_position_notional: float = Field(gt=0)
    max_daily_loss: float = Field(gt=0)
    max_slippage_bps: float | None = None
    max_impact_bps: float | None = None
    min_top_depth_usd: float | None = None
    min_depth_near_price_usd: float | None = None
    max_book_age_ms: int | None = None
    max_trade_age_ms: int | None = None
    max_drawdown: float | None = None
    cooldown_after_loss: int | None = None
    cooldown_after_reject: int | None = None
    venue_exposure_limit: float | None = None
    instrument_exposure_limit: float | None = None


# ---------------------------------------------------------------------------
# Evidence requirements
# ---------------------------------------------------------------------------

class EvidenceRequirement(StrictModel):
    required_feature_hash: str | None = None
    required_policy_hash: str | None = None
    required_replay_dataset_ref: str | None = None
    required_backtest_result_ref: str | None = None
    required_compile_artifact_ref: str | None = None
    required_manual_review_ref: str | None = None


# ---------------------------------------------------------------------------
# StrategySpecV2 — the full v2 model
# ---------------------------------------------------------------------------

class StrategySpecV2(StrictModel):
    """Complete StrategySpec v2 for ND microstructure strategies.

    Safety contract:
    - execution_authority is always False
    - No live order authority is introduced
    """
    metadata: StrategySpecV2Metadata
    universe: StrategySpecV2Universe
    feature_inputs: list[FeatureInput] = Field(min_length=1)
    conditions: list[ConditionDSL] = Field(default_factory=list)
    event_detectors: list[EventDetector] | None = None
    archetype: Archetype | None = None
    overlays: list[Overlay] | None = None
    risk_contract: RiskContractV2
    evidence_requirements: EvidenceRequirement | None = None
    source_health_requirements: list[SourceHealthRequirement] | None = None
    execution_authority: Literal[False] = False

    @model_validator(mode="after")
    def validate_no_execution_authority(self) -> "StrategySpecV2":
        if self.execution_authority is not False:
            raise ValueError("StrategySpecV2 must have execution_authority=False")
        return self
