"""Replay fixture types and configuration for expanded validation."""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ReplayFixtureType(str, Enum):
    """Supported replay fixture data types."""
    BARS = "bars"
    TRADES = "trades"
    QUOTES = "quotes"
    ORDER_BOOK_SNAPSHOTS = "order_book_snapshots"
    FUNDING_RATES = "funding_rates"
    LIQUIDATIONS = "liquidations"


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
