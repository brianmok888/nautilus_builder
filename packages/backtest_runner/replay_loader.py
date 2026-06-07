"""Deterministic replay fixture generation and validation.

Generates reproducible fixture data from a seed for each dataset type.
Same seed + same config always produces the same fixture and the same hash.
"""
from __future__ import annotations

import hashlib
import json
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .replay_fixtures import (
    BarFixture,
    BadDataFixture,
    BaseFixture,
    FundingRateFixture,
    LiquidationFixture,
    OrderBookSnapshotFixture,
    QuoteFixture,
    ReplayFixtureType,
    StaleDataFixture,
    TradeFixture,
    compute_fixture_hash,
)


class FixtureGenerationError(Exception):
    """Raised when fixture generation fails validation."""


class FixtureSpec(BaseModel):
    """Specification for generating a deterministic fixture."""
    model_config = ConfigDict(extra="forbid")

    fixture_type: ReplayFixtureType
    instrument_id: str = Field(min_length=1)
    num_rows: int = Field(ge=1, le=10_000)
    seed: int = 0
    base_price: float = Field(gt=0)
    tick_size: float = Field(gt=0)


class ReplayDatasetReport(BaseModel):
    """Report from a loaded replay dataset with determinism proof."""
    model_config = ConfigDict(extra="forbid")

    spec_hash: str
    fixture_hash: str
    row_count: int
    fixture_type: ReplayFixtureType
    instrument_id: str
    seed: int
    determinism_verified: bool
    credentials_used: Literal[False] = False
    live_trading_enabled: Literal[False] = False
    execution_authority: Literal[False] = False


def _prng(seed: int) -> float:
    """Simple deterministic pseudo-random float in [0, 1) from seed."""
    h = hashlib.sha256(f"nautilus_builder_replay:{seed}".encode()).hexdigest()
    return int(h[:8], 16) / 0x100000000


def _prng_sequence(seed: int, n: int) -> list[float]:
    """Generate n deterministic floats in [0, 1)."""
    return [_prng(seed + i) for i in range(n)]


def generate_fixture(spec: FixtureSpec) -> BaseFixture:
    """Generate a deterministic fixture from a specification.

    Same spec always produces the same fixture data.
    """
    n = spec.num_rows
    s = spec.seed
    p = spec.base_price
    t = spec.tick_size

    timestamps: list[int] = [1_000_000_000_000 + (i + 1) * 1_000_000_000 for i in range(n)]

    if spec.fixture_type == ReplayFixtureType.BARS:
        rng = _prng_sequence(s, n * 5)
        opens = [round(p + (rng[i * 5] - 0.5) * t * 100, 2) for i in range(n)]
        closes = [round(p + (rng[i * 5 + 1] - 0.5) * t * 100, 2) for i in range(n)]
        highs = [round(max(opens[i], closes[i]) + rng[i * 5 + 2] * t * 50, 2) for i in range(n)]
        lows = [round(min(opens[i], closes[i]) - rng[i * 5 + 3] * t * 50, 2) for i in range(n)]
        volumes = [round(rng[i * 5 + 4] * 100, 2) for i in range(n)]
        return BarFixture(
            fixture_type=spec.fixture_type,
            instrument_id=spec.instrument_id,
            timestamp_ns=timestamps,
            open=opens,
            high=highs,
            low=lows,
            close=closes,
            volume=volumes,
            seed=s,
        )

    elif spec.fixture_type == ReplayFixtureType.TRADES:
        rng = _prng_sequence(s, n * 3)
        prices = [round(p + (rng[i * 3] - 0.5) * t * 100, 2) for i in range(n)]
        sizes = [round(rng[i * 3 + 1] * 10, 4) for i in range(n)]
        sides = ["BUY" if rng[i * 3 + 2] > 0.5 else "SELL" for i in range(n)]
        return TradeFixture(
            fixture_type=spec.fixture_type,
            instrument_id=spec.instrument_id,
            timestamp_ns=timestamps,
            price=prices,
            size=sizes,
            side=sides,
            seed=s,
        )

    elif spec.fixture_type == ReplayFixtureType.QUOTES:
        rng = _prng_sequence(s, n * 4)
        mid = p
        bids = [round(mid - rng[i * 4] * t * 50, 2) for i in range(n)]
        asks = [round(mid + rng[i * 4 + 1] * t * 50, 2) for i in range(n)]
        bid_sizes = [round(rng[i * 4 + 2] * 100, 4) for i in range(n)]
        ask_sizes = [round(rng[i * 4 + 3] * 100, 4) for i in range(n)]
        return QuoteFixture(
            fixture_type=spec.fixture_type,
            instrument_id=spec.instrument_id,
            timestamp_ns=timestamps,
            bid=bids,
            ask=asks,
            bid_size=bid_sizes,
            ask_size=ask_sizes,
            seed=s,
        )

    elif spec.fixture_type == ReplayFixtureType.ORDER_BOOK_SNAPSHOTS:
        rng = _prng_sequence(s, n * 10)
        depth = 5
        bids: list[list[float]] = []
        asks: list[list[float]] = []
        for i in range(n):
            level_bids: list[float] = []
            level_asks: list[float] = []
            for d in range(depth):
                level_bids.extend([
                    round(p - (d + 1) * t - rng[i * 10 + d * 2] * t, 2),
                    round(rng[i * 10 + d * 2 + 1] * 50, 2),
                ])
                level_asks.extend([
                    round(p + (d + 1) * t + rng[i * 10 + d * 2] * t, 2),
                    round(rng[i * 10 + d * 2 + 1] * 50, 2),
                ])
            bids.append(level_bids)
            asks.append(level_asks)
        return OrderBookSnapshotFixture(
            fixture_type=spec.fixture_type,
            instrument_id=spec.instrument_id,
            timestamp_ns=timestamps,
            bids=bids,
            asks=asks,
            depth=depth,
            seed=s,
        )

    elif spec.fixture_type == ReplayFixtureType.FUNDING_RATES:
        rng = _prng_sequence(s, n * 2)
        rates = [round((rng[i * 2] - 0.5) * 0.001, 8) for i in range(n)]
        next_times = [timestamps[i] + 8 * 3_600_000_000_000 for i in range(n)]
        return FundingRateFixture(
            fixture_type=spec.fixture_type,
            instrument_id=spec.instrument_id,
            timestamp_ns=timestamps,
            rate=rates,
            next_funding_time_ns=next_times,
            seed=s,
        )

    elif spec.fixture_type == ReplayFixtureType.LIQUIDATIONS:
        rng = _prng_sequence(s, n * 3)
        prices = [round(p + (rng[i * 3] - 0.5) * t * 200, 2) for i in range(n)]
        sizes = [round(rng[i * 3 + 1] * 5, 4) for i in range(n)]
        sides = ["BUY" if rng[i * 3 + 2] > 0.5 else "SELL" for i in range(n)]
        return LiquidationFixture(
            fixture_type=spec.fixture_type,
            instrument_id=spec.instrument_id,
            timestamp_ns=timestamps,
            price=prices,
            size=sizes,
            side=sides,
            seed=s,
        )

    elif spec.fixture_type == ReplayFixtureType.BAD_DATA_CASES:
        rng = _prng_sequence(s, n)
        anomalies = [
            "zero_price" if r < 0.25 else
            "negative_size" if r < 0.5 else
            "crossed_book" if r < 0.75 else
            "out_of_order_timestamp"
            for r in rng
        ]
        return BadDataFixture(
            fixture_type=spec.fixture_type,
            instrument_id=spec.instrument_id,
            timestamp_ns=timestamps,
            anomaly_type=anomalies[0],
            description="Bad data case generated by deterministic loader",
            seed=s,
        )

    elif spec.fixture_type == ReplayFixtureType.STALE_DATA_CASES:
        rng = _prng_sequence(s, n)
        staleness = [int(r * 30_000) + 1 for r in rng]
        return StaleDataFixture(
            fixture_type=spec.fixture_type,
            instrument_id=spec.instrument_id,
            timestamp_ns=timestamps,
            staleness_ms=staleness[0],
            description="Stale data case generated by deterministic loader",
            seed=s,
        )

    else:
        # feature_snapshots and state_bundle_exports use a generic approach
        rng = _prng_sequence(s, n)
        values = [round(r * 100, 4) for r in rng]
        return BarFixture(
            fixture_type=ReplayFixtureType.BARS,
            instrument_id=spec.instrument_id,
            timestamp_ns=timestamps,
            open=values,
            high=values,
            low=values,
            close=values,
            volume=[1.0] * n,
            seed=s,
        )


def generate_dataset_report(spec: FixtureSpec) -> ReplayDatasetReport:
    """Generate a full dataset report with determinism proof.

    Creates the fixture, computes its hash, and verifies determinism
    by generating a second fixture and comparing hashes.
    """
    fixture = generate_fixture(spec)
    hash1 = compute_fixture_hash(fixture)

    # Verify determinism: generate again, must produce same hash
    fixture2 = generate_fixture(spec)
    hash2 = compute_fixture_hash(fixture2)

    determinism_verified = hash1 == hash2

    return ReplayDatasetReport(
        spec_hash=_compute_spec_hash(spec),
        fixture_hash=hash1,
        row_count=spec.num_rows,
        fixture_type=spec.fixture_type,
        instrument_id=spec.instrument_id,
        seed=spec.seed,
        determinism_verified=determinism_verified,
    )


def validate_ohlc_consistency(fixture: BarFixture) -> list[str]:
    """Validate OHLC consistency for bar fixtures.

    Returns list of violations (empty if valid).
    Rules: low <= open <= high, low <= close <= high.
    """
    violations: list[str] = []
    for i in range(len(fixture.timestamp_ns)):
        op, hi, lo, cl = fixture.open[i], fixture.high[i], fixture.low[i], fixture.close[i]
        if lo > op:
            violations.append(f"row {i}: low({lo}) > open({op})")
        if lo > cl:
            violations.append(f"row {i}: low({lo}) > close({cl})")
        if op > hi:
            violations.append(f"row {i}: open({op}) > high({hi})")
        if cl > hi:
            violations.append(f"row {i}: close({cl}) > high({hi})")
    return violations


def _compute_spec_hash(spec: FixtureSpec) -> str:
    """Compute SHA-256 of the spec for determinism tracking."""
    data = spec.model_dump(mode="json")
    canonical = json.dumps(data, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()
