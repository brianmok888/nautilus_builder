"""Replay fixture types, schemas, and deterministic hashing for expanded validation."""
from __future__ import annotations

import hashlib
import json
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ReplayFixtureType(str, Enum):
    """Supported replay fixture data types."""
    BARS = "bars"
    TRADES = "trades"
    QUOTES = "quotes"
    ORDER_BOOK_SNAPSHOTS = "order_book_snapshots"
    FUNDING_RATES = "funding_rates"
    LIQUIDATIONS = "liquidations"
    FEATURE_SNAPSHOTS = "feature_snapshots"
    STATE_BUNDLE_EXPORTS = "state_bundle_exports"
    BAD_DATA_CASES = "bad_data_cases"
    STALE_DATA_CASES = "stale_data_cases"


class SourceHealthStatus(str, Enum):
    """Health status of a feature data source."""
    SOURCE_AVAILABLE = "source_available"
    STALE = "stale"
    MISSING = "missing"
    TRUE_ZERO = "true_zero"
    SYNTHETIC_FALLBACK_USED = "synthetic_fallback_used"


class BaseFixture(BaseModel):
    """Base model for all replay fixtures."""
    model_config = ConfigDict(extra="forbid")

    fixture_type: ReplayFixtureType
    instrument_id: str = Field(min_length=1)
    timestamp_ns: list[int]
    seed: int = 0

    @field_validator("timestamp_ns")
    @classmethod
    def _validate_timestamps(cls, v: list[int]) -> list[int]:
        if len(v) < 1:
            raise ValueError("timestamp_ns must contain at least one entry")
        for i in range(1, len(v)):
            if v[i] <= v[i - 1]:
                raise ValueError(
                    f"timestamp_ns must be strictly monotonically increasing; "
                    f"got {v[i]} at index {i} which is <= {v[i - 1]} at index {i - 1}"
                )
        return v


class BarFixture(BaseFixture):
    """OHLCV bar replay fixture."""
    open: list[float]
    high: list[float]
    low: list[float]
    close: list[float]
    volume: list[float]


class TradeFixture(BaseFixture):
    """Trade tick replay fixture."""
    price: list[float]
    size: list[float]
    side: list[str]


class QuoteFixture(BaseFixture):
    """Quote tick replay fixture."""
    bid: list[float]
    ask: list[float]
    bid_size: list[float]
    ask_size: list[float]


class OrderBookSnapshotFixture(BaseFixture):
    """Order book snapshot replay fixture."""
    bids: list[list[float]]
    asks: list[list[float]]
    depth: int


class FundingRateFixture(BaseFixture):
    """Funding rate replay fixture."""
    rate: list[float]
    next_funding_time_ns: list[int]


class LiquidationFixture(BaseFixture):
    """Liquidation event replay fixture."""
    price: list[float]
    size: list[float]
    side: list[str]


class FeatureSnapshotFixture(BaseFixture):
    """Feature snapshot replay fixture with source health tracking."""
    feature_name: str
    values: list[float]
    source_health: SourceHealthStatus


class StateBundleExportFixture(BaseFixture):
    """State bundle export replay fixture."""
    bundle_type: str
    state_data: dict


class BadDataFixture(BaseFixture):
    """Bad data test case fixture."""
    anomaly_type: str
    description: str


class StaleDataFixture(BaseFixture):
    """Stale data test case fixture."""
    staleness_ms: int
    description: str


class ReplayReportEvidence(BaseModel):
    """Evidence from a replay run with expanded dataset tracking.

    Safety contract: credentials_used, live_trading_enabled, and
    execution_authority are locked to False for all Builder replay.
    """
    model_config = ConfigDict(extra="forbid")

    dataset_type: ReplayFixtureType
    dataset_hash: str
    row_count: int
    instrument_ids: list[str]
    time_range: str
    bad_data_count: int
    stale_data_count: int
    missing_data_count: int
    synthetic_data_used: bool
    credentials_used: Literal[False] = False
    live_trading_enabled: Literal[False] = False
    execution_authority: Literal[False] = False


class FailureModeFixture(BaseModel):
    """A failure mode that replay fixtures should test."""
    model_config = ConfigDict(extra="forbid")

    mode: str
    description: str


class ReplayFixtureConfig(BaseModel):
    """Configuration for a replay fixture dataset."""
    model_config = ConfigDict(extra="forbid")

    fixture_name: str
    instrument_id: str
    data_types: list[str] = Field(min_length=1)
    failure_modes: list[FailureModeFixture] = Field(default_factory=list)


def compute_fixture_hash(fixture: BaseFixture) -> str:
    """Compute SHA-256 hash of fixture data for deterministic verification."""
    data = fixture.model_dump(mode="json")
    canonical = json.dumps(data, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()


def validate_replay_fixture_config(config: ReplayFixtureConfig) -> None:
    """Validate a replay fixture config for completeness."""
    if not config.instrument_id.strip():
        raise ValueError("instrument_id must not be empty")
    if not config.data_types:
        raise ValueError("at least one data type is required")
    valid_types = {t.value for t in ReplayFixtureType}
    for dt in config.data_types:
        if dt not in valid_types:
            raise ValueError(f"unknown data type: {dt}. Valid: {sorted(valid_types)}")
