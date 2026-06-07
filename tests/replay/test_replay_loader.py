"""Tests for deterministic replay fixture generation, hashing, and OHLC validation."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from packages.backtest_runner.replay_loader import (
    FixtureSpec,
    ReplayDatasetReport,
    generate_dataset_report,
    generate_fixture,
    validate_ohlc_consistency,
)
from packages.backtest_runner.replay_fixtures import (
    BarFixture,
    TradeFixture,
    QuoteFixture,
    OrderBookSnapshotFixture,
    FundingRateFixture,
    LiquidationFixture,
    BadDataFixture,
    StaleDataFixture,
    ReplayFixtureType,
    compute_fixture_hash,
)


# ---------------------------------------------------------------------------
# FixtureSpec validation
# ---------------------------------------------------------------------------

class TestFixtureSpec:
    def test_valid_spec(self):
        spec = FixtureSpec(
            fixture_type=ReplayFixtureType.BARS,
            instrument_id="BTCUSDT-PERP.BINANCE",
            num_rows=10,
            seed=42,
            base_price=50000.0,
            tick_size=0.01,
        )
        assert spec.num_rows == 10

    def test_rejects_zero_rows(self):
        with pytest.raises(ValidationError):
            FixtureSpec(
                fixture_type=ReplayFixtureType.BARS,
                instrument_id="BTCUSDT-PERP.BINANCE",
                num_rows=0,
                seed=0,
                base_price=50000.0,
                tick_size=0.01,
            )

    def test_rejects_negative_base_price(self):
        with pytest.raises(ValidationError):
            FixtureSpec(
                fixture_type=ReplayFixtureType.BARS,
                instrument_id="BTCUSDT-PERP.BINANCE",
                num_rows=10,
                seed=0,
                base_price=-1.0,
                tick_size=0.01,
            )

    def test_rejects_zero_tick_size(self):
        with pytest.raises(ValidationError):
            FixtureSpec(
                fixture_type=ReplayFixtureType.BARS,
                instrument_id="BTCUSDT-PERP.BINANCE",
                num_rows=10,
                seed=0,
                base_price=50000.0,
                tick_size=0.0,
            )

    def test_rejects_empty_instrument_id(self):
        with pytest.raises(ValidationError):
            FixtureSpec(
                fixture_type=ReplayFixtureType.BARS,
                instrument_id="",
                num_rows=10,
                seed=0,
                base_price=50000.0,
                tick_size=0.01,
            )

    def test_rejects_extra_fields(self):
        with pytest.raises(ValidationError):
            FixtureSpec(
                fixture_type=ReplayFixtureType.BARS,
                instrument_id="BTCUSDT-PERP.BINANCE",
                num_rows=10,
                seed=0,
                base_price=50000.0,
                tick_size=0.01,
                bogus="nope",
            )


# ---------------------------------------------------------------------------
# Deterministic generation: same seed -> same fixture
# ---------------------------------------------------------------------------

class TestDeterministicGeneration:
    def _bars_spec(self, seed: int = 42) -> FixtureSpec:
        return FixtureSpec(
            fixture_type=ReplayFixtureType.BARS,
            instrument_id="BTCUSDT-PERP.BINANCE",
            num_rows=20,
            seed=seed,
            base_price=50000.0,
            tick_size=0.01,
        )

    def test_same_seed_produces_same_bar_fixture(self):
        spec = self._bars_spec(seed=42)
        f1 = generate_fixture(spec)
        f2 = generate_fixture(spec)
        assert compute_fixture_hash(f1) == compute_fixture_hash(f2)

    def test_different_seed_produces_different_bar_fixture(self):
        f1 = generate_fixture(self._bars_spec(seed=42))
        f2 = generate_fixture(self._bars_spec(seed=99))
        assert compute_fixture_hash(f1) != compute_fixture_hash(f2)

    def test_bar_fixture_has_correct_row_count(self):
        f = generate_fixture(self._bars_spec())
        assert isinstance(f, BarFixture)
        assert len(f.timestamp_ns) == 20
        assert len(f.open) == 20
        assert len(f.high) == 20
        assert len(f.low) == 20
        assert len(f.close) == 20
        assert len(f.volume) == 20

    def test_bar_fixture_ohlc_consistency(self):
        f = generate_fixture(self._bars_spec())
        assert isinstance(f, BarFixture)
        violations = validate_ohlc_consistency(f)
        assert violations == [], f"OHLC violations: {violations[:5]}"

    def test_trade_fixture_deterministic(self):
        spec = FixtureSpec(
            fixture_type=ReplayFixtureType.TRADES,
            instrument_id="ETHUSDT-PERP.BINANCE",
            num_rows=15,
            seed=7,
            base_price=3000.0,
            tick_size=0.01,
        )
        f1 = generate_fixture(spec)
        f2 = generate_fixture(spec)
        assert isinstance(f1, TradeFixture)
        assert compute_fixture_hash(f1) == compute_fixture_hash(f2)

    def test_quote_fixture_deterministic(self):
        spec = FixtureSpec(
            fixture_type=ReplayFixtureType.QUOTES,
            instrument_id="BTCUSDT-PERP.BINANCE",
            num_rows=10,
            seed=123,
            base_price=50000.0,
            tick_size=0.01,
        )
        f1 = generate_fixture(spec)
        f2 = generate_fixture(spec)
        assert isinstance(f1, QuoteFixture)
        assert compute_fixture_hash(f1) == compute_fixture_hash(f2)

    def test_order_book_snapshot_deterministic(self):
        spec = FixtureSpec(
            fixture_type=ReplayFixtureType.ORDER_BOOK_SNAPSHOTS,
            instrument_id="BTCUSDT-PERP.BINANCE",
            num_rows=5,
            seed=1,
            base_price=50000.0,
            tick_size=0.01,
        )
        f1 = generate_fixture(spec)
        f2 = generate_fixture(spec)
        assert isinstance(f1, OrderBookSnapshotFixture)
        assert compute_fixture_hash(f1) == compute_fixture_hash(f2)
        assert f1.depth == 5

    def test_funding_rate_deterministic(self):
        spec = FixtureSpec(
            fixture_type=ReplayFixtureType.FUNDING_RATES,
            instrument_id="BTCUSDT-PERP.BINANCE",
            num_rows=8,
            seed=55,
            base_price=50000.0,
            tick_size=0.01,
        )
        f1 = generate_fixture(spec)
        f2 = generate_fixture(spec)
        assert isinstance(f1, FundingRateFixture)
        assert compute_fixture_hash(f1) == compute_fixture_hash(f2)

    def test_liquidation_deterministic(self):
        spec = FixtureSpec(
            fixture_type=ReplayFixtureType.LIQUIDATIONS,
            instrument_id="BTCUSDT-PERP.BINANCE",
            num_rows=10,
            seed=99,
            base_price=50000.0,
            tick_size=0.01,
        )
        f1 = generate_fixture(spec)
        f2 = generate_fixture(spec)
        assert isinstance(f1, LiquidationFixture)
        assert compute_fixture_hash(f1) == compute_fixture_hash(f2)

    def test_bad_data_fixture_deterministic(self):
        spec = FixtureSpec(
            fixture_type=ReplayFixtureType.BAD_DATA_CASES,
            instrument_id="BTCUSDT-PERP.BINANCE",
            num_rows=5,
            seed=3,
            base_price=50000.0,
            tick_size=0.01,
        )
        f1 = generate_fixture(spec)
        f2 = generate_fixture(spec)
        assert isinstance(f1, BadDataFixture)
        assert compute_fixture_hash(f1) == compute_fixture_hash(f2)

    def test_stale_data_fixture_deterministic(self):
        spec = FixtureSpec(
            fixture_type=ReplayFixtureType.STALE_DATA_CASES,
            instrument_id="BTCUSDT-PERP.BINANCE",
            num_rows=5,
            seed=77,
            base_price=50000.0,
            tick_size=0.01,
        )
        f1 = generate_fixture(spec)
        f2 = generate_fixture(spec)
        assert isinstance(f1, StaleDataFixture)
        assert compute_fixture_hash(f1) == compute_fixture_hash(f2)


# ---------------------------------------------------------------------------
# Dataset report: determinism proof + safety contract
# ---------------------------------------------------------------------------

class TestDatasetReport:
    def _make_report(self, fixture_type: ReplayFixtureType = ReplayFixtureType.BARS) -> ReplayDatasetReport:
        spec = FixtureSpec(
            fixture_type=fixture_type,
            instrument_id="BTCUSDT-PERP.BINANCE",
            num_rows=10,
            seed=42,
            base_price=50000.0,
            tick_size=0.01,
        )
        return generate_dataset_report(spec)

    def test_report_verifies_determinism(self):
        report = self._make_report()
        assert report.determinism_verified is True

    def test_report_has_spec_hash(self):
        report = self._make_report()
        assert len(report.spec_hash) == 64  # SHA-256 hex

    def test_report_has_fixture_hash(self):
        report = self._make_report()
        assert len(report.fixture_hash) == 64  # SHA-256 hex

    def test_report_row_count(self):
        report = self._make_report()
        assert report.row_count == 10

    def test_report_safety_contract(self):
        report = self._make_report()
        assert report.credentials_used is False
        assert report.live_trading_enabled is False
        assert report.execution_authority is False

    def test_report_rejects_true_authority(self):
        with pytest.raises(ValidationError):
            ReplayDatasetReport(
                spec_hash="a" * 64,
                fixture_hash="b" * 64,
                row_count=10,
                fixture_type=ReplayFixtureType.BARS,
                instrument_id="BTCUSDT-PERP.BINANCE",
                seed=0,
                determinism_verified=True,
                execution_authority=True,
            )

    def test_report_for_all_types(self):
        for ft in ReplayFixtureType:
            report = self._make_report(ft)
            assert report.determinism_verified is True
            assert report.fixture_type == ft


# ---------------------------------------------------------------------------
# OHLC validation
# ---------------------------------------------------------------------------

class TestOhlcValidation:
    def test_valid_bars_pass(self):
        spec = FixtureSpec(
            fixture_type=ReplayFixtureType.BARS,
            instrument_id="BTCUSDT-PERP.BINANCE",
            num_rows=50,
            seed=1,
            base_price=50000.0,
            tick_size=0.01,
        )
        f = generate_fixture(spec)
        assert isinstance(f, BarFixture)
        violations = validate_ohlc_consistency(f)
        assert violations == []

    def test_manual_invalid_bar_detected(self):
        f = BarFixture(
            fixture_type=ReplayFixtureType.BARS,
            instrument_id="BTCUSDT-PERP.BINANCE",
            timestamp_ns=[1000, 2000],
            open=[50000.0, 99999.0],  # row 1: open > high
            high=[50100.0, 50000.0],
            low=[49900.0, 49900.0],
            close=[50050.0, 50050.0],
            volume=[10.0, 10.0],
        )
        violations = validate_ohlc_consistency(f)
        assert len(violations) > 0
        assert any("open" in v and "high" in v for v in violations)

    def test_low_above_close_detected(self):
        f = BarFixture(
            fixture_type=ReplayFixtureType.BARS,
            instrument_id="BTCUSDT-PERP.BINANCE",
            timestamp_ns=[1000],
            open=[50000.0],
            high=[50100.0],
            low=[50050.0],  # low > open
            close=[50020.0],  # low > close
            volume=[10.0],
        )
        violations = validate_ohlc_consistency(f)
        assert len(violations) >= 2
