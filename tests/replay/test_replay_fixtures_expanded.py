"""Tests for expanded replay fixture types, schemas, deterministic hashing, and safety contracts."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from packages.backtest_runner.replay_fixtures import (
    ReplayFixtureType,
    SourceHealthStatus,
    BarFixture,
    TradeFixture,
    QuoteFixture,
    OrderBookSnapshotFixture,
    FundingRateFixture,
    LiquidationFixture,
    FeatureSnapshotFixture,
    StateBundleExportFixture,
    BadDataFixture,
    StaleDataFixture,
    ReplayReportEvidence,
    compute_fixture_hash,
)


# ---------------------------------------------------------------------------
# 1. ReplayFixtureType: all 10 values exist (6 original + 4 new)
# ---------------------------------------------------------------------------

class TestReplayFixtureTypeExpanded:
    def test_original_six_types_exist(self):
        assert ReplayFixtureType.BARS.value == "bars"
        assert ReplayFixtureType.TRADES.value == "trades"
        assert ReplayFixtureType.QUOTES.value == "quotes"
        assert ReplayFixtureType.ORDER_BOOK_SNAPSHOTS.value == "order_book_snapshots"
        assert ReplayFixtureType.FUNDING_RATES.value == "funding_rates"
        assert ReplayFixtureType.LIQUIDATIONS.value == "liquidations"

    def test_four_new_types_exist(self):
        assert ReplayFixtureType.FEATURE_SNAPSHOTS.value == "feature_snapshots"
        assert ReplayFixtureType.STATE_BUNDLE_EXPORTS.value == "state_bundle_exports"
        assert ReplayFixtureType.BAD_DATA_CASES.value == "bad_data_cases"
        assert ReplayFixtureType.STALE_DATA_CASES.value == "stale_data_cases"

    def test_total_type_count_is_ten(self):
        assert len(ReplayFixtureType) == 10


# ---------------------------------------------------------------------------
# 2. SourceHealthStatus enum
# ---------------------------------------------------------------------------

class TestSourceHealthStatus:
    def test_all_five_values_exist(self):
        assert SourceHealthStatus.SOURCE_AVAILABLE.value == "source_available"
        assert SourceHealthStatus.STALE.value == "stale"
        assert SourceHealthStatus.MISSING.value == "missing"
        assert SourceHealthStatus.TRUE_ZERO.value == "true_zero"
        assert SourceHealthStatus.SYNTHETIC_FALLBACK_USED.value == "synthetic_fallback_used"

    def test_total_status_count_is_five(self):
        assert len(SourceHealthStatus) == 5


# ---------------------------------------------------------------------------
# 3. Fixture schema validation: each type creates and validates correctly
# ---------------------------------------------------------------------------

class TestBarFixture:
    def test_valid_bar_fixture(self):
        f = BarFixture(
            fixture_type=ReplayFixtureType.BARS,
            instrument_id="BTCUSDT-PERP.BINANCE",
            timestamp_ns=[1000, 2000, 3000],
            open=[50000.0, 50100.0, 50200.0],
            high=[50100.0, 50200.0, 50300.0],
            low=[49900.0, 50000.0, 50100.0],
            close=[50100.0, 50200.0, 50300.0],
            volume=[10.0, 12.0, 8.0],
        )
        assert f.fixture_type == ReplayFixtureType.BARS
        assert len(f.close) == 3

    def test_bar_fixture_rejects_extra_fields(self):
        with pytest.raises(ValidationError):
            BarFixture(
                fixture_type=ReplayFixtureType.BARS,
                instrument_id="BTCUSDT-PERP.BINANCE",
                timestamp_ns=[1000],
                open=[50000.0],
                high=[50100.0],
                low=[49900.0],
                close=[50100.0],
                volume=[10.0],
                unexpected_field="bad",
            )

    def test_bar_fixture_rejects_missing_close(self):
        with pytest.raises(ValidationError):
            BarFixture(
                fixture_type=ReplayFixtureType.BARS,
                instrument_id="BTCUSDT-PERP.BINANCE",
                timestamp_ns=[1000],
                open=[50000.0],
                high=[50100.0],
                low=[49900.0],
                volume=[10.0],
            )


class TestTradeFixture:
    def test_valid_trade_fixture(self):
        f = TradeFixture(
            fixture_type=ReplayFixtureType.TRADES,
            instrument_id="ETHUSDT-PERP.BINANCE",
            timestamp_ns=[1000, 2000],
            price=[3000.0, 3001.0],
            size=[0.5, 1.2],
            side=["BUY", "SELL"],
        )
        assert len(f.side) == 2

    def test_trade_fixture_rejects_extra_fields(self):
        with pytest.raises(ValidationError):
            TradeFixture(
                fixture_type=ReplayFixtureType.TRADES,
                instrument_id="ETHUSDT-PERP.BINANCE",
                timestamp_ns=[1000],
                price=[3000.0],
                size=[0.5],
                side=["BUY"],
                bogus=True,
            )


class TestQuoteFixture:
    def test_valid_quote_fixture(self):
        f = QuoteFixture(
            fixture_type=ReplayFixtureType.QUOTES,
            instrument_id="BTCUSDT-PERP.BINANCE",
            timestamp_ns=[1000],
            bid=[50000.0],
            ask=[50010.0],
            bid_size=[1.0],
            ask_size=[0.8],
        )
        assert len(f.bid) == 1

    def test_quote_fixture_rejects_extra_fields(self):
        with pytest.raises(ValidationError):
            QuoteFixture(
                fixture_type=ReplayFixtureType.QUOTES,
                instrument_id="BTCUSDT-PERP.BINANCE",
                timestamp_ns=[1000],
                bid=[50000.0],
                ask=[50010.0],
                bid_size=[1.0],
                ask_size=[0.8],
                spread_bps=2.0,
            )


class TestOrderBookSnapshotFixture:
    def test_valid_orderbook_fixture(self):
        f = OrderBookSnapshotFixture(
            fixture_type=ReplayFixtureType.ORDER_BOOK_SNAPSHOTS,
            instrument_id="BTCUSDT-PERP.BINANCE",
            timestamp_ns=[1000],
            bids=[[50000.0, 1.0], [49999.0, 2.0]],
            asks=[[50001.0, 0.5], [50002.0, 1.5]],
            depth=2,
        )
        assert f.depth == 2
        assert len(f.bids) == 2

    def test_orderbook_fixture_rejects_extra_fields(self):
        with pytest.raises(ValidationError):
            OrderBookSnapshotFixture(
                fixture_type=ReplayFixtureType.ORDER_BOOK_SNAPSHOTS,
                instrument_id="BTCUSDT-PERP.BINANCE",
                timestamp_ns=[1000],
                bids=[[50000.0, 1.0]],
                asks=[[50001.0, 0.5]],
                depth=1,
                unknown=True,
            )


class TestFundingRateFixture:
    def test_valid_funding_fixture(self):
        f = FundingRateFixture(
            fixture_type=ReplayFixtureType.FUNDING_RATES,
            instrument_id="BTCUSDT-PERP.BINANCE",
            timestamp_ns=[1000],
            rate=[0.0001],
            next_funding_time_ns=[2000],
        )
        assert f.rate[0] == pytest.approx(0.0001)

    def test_funding_fixture_rejects_extra_fields(self):
        with pytest.raises(ValidationError):
            FundingRateFixture(
                fixture_type=ReplayFixtureType.FUNDING_RATES,
                instrument_id="BTCUSDT-PERP.BINANCE",
                timestamp_ns=[1000],
                rate=[0.0001],
                next_funding_time_ns=[2000],
                extra=True,
            )


class TestLiquidationFixture:
    def test_valid_liquidation_fixture(self):
        f = LiquidationFixture(
            fixture_type=ReplayFixtureType.LIQUIDATIONS,
            instrument_id="BTCUSDT-PERP.BINANCE",
            timestamp_ns=[1000],
            price=[49000.0],
            size=[5.0],
            side=["SELL"],
        )
        assert len(f.side) == 1

    def test_liquidation_fixture_rejects_extra_fields(self):
        with pytest.raises(ValidationError):
            LiquidationFixture(
                fixture_type=ReplayFixtureType.LIQUIDATIONS,
                instrument_id="BTCUSDT-PERP.BINANCE",
                timestamp_ns=[1000],
                price=[49000.0],
                size=[5.0],
                side=["SELL"],
                not_valid=True,
            )


class TestFeatureSnapshotFixture:
    def test_valid_feature_snapshot_fixture(self):
        f = FeatureSnapshotFixture(
            fixture_type=ReplayFixtureType.FEATURE_SNAPSHOTS,
            instrument_id="BTCUSDT-PERP.BINANCE",
            timestamp_ns=[1000],
            feature_name="obi",
            values=[0.15, -0.32, 0.08],
            source_health=SourceHealthStatus.SOURCE_AVAILABLE,
        )
        assert f.feature_name == "obi"
        assert f.source_health == SourceHealthStatus.SOURCE_AVAILABLE

    def test_feature_snapshot_with_stale_health(self):
        f = FeatureSnapshotFixture(
            fixture_type=ReplayFixtureType.FEATURE_SNAPSHOTS,
            instrument_id="BTCUSDT-PERP.BINANCE",
            timestamp_ns=[1000],
            feature_name="cvd",
            values=[100.0],
            source_health=SourceHealthStatus.STALE,
        )
        assert f.source_health == SourceHealthStatus.STALE

    def test_feature_snapshot_rejects_extra_fields(self):
        with pytest.raises(ValidationError):
            FeatureSnapshotFixture(
                fixture_type=ReplayFixtureType.FEATURE_SNAPSHOTS,
                instrument_id="BTCUSDT-PERP.BINANCE",
                timestamp_ns=[1000],
                feature_name="obi",
                values=[0.15],
                source_health=SourceHealthStatus.SOURCE_AVAILABLE,
                rogue_field="yes",
            )


class TestStateBundleExportFixture:
    def test_valid_state_bundle_fixture(self):
        f = StateBundleExportFixture(
            fixture_type=ReplayFixtureType.STATE_BUNDLE_EXPORTS,
            instrument_id="BTCUSDT-PERP.BINANCE",
            timestamp_ns=[1000],
            bundle_type="actor_state",
            state_data={"positions": {"long": 1}, "signals": {"regime": "trending"}},
        )
        assert f.bundle_type == "actor_state"

    def test_state_bundle_rejects_extra_fields(self):
        with pytest.raises(ValidationError):
            StateBundleExportFixture(
                fixture_type=ReplayFixtureType.STATE_BUNDLE_EXPORTS,
                instrument_id="BTCUSDT-PERP.BINANCE",
                timestamp_ns=[1000],
                bundle_type="actor_state",
                state_data={},
                sneaky=True,
            )


class TestBadDataFixture:
    def test_valid_bad_data_fixture(self):
        f = BadDataFixture(
            fixture_type=ReplayFixtureType.BAD_DATA_CASES,
            instrument_id="BTCUSDT-PERP.BINANCE",
            timestamp_ns=[1000],
            anomaly_type="negative_price",
            description="Price is negative",
        )
        assert f.anomaly_type == "negative_price"

    def test_bad_data_rejects_extra_fields(self):
        with pytest.raises(ValidationError):
            BadDataFixture(
                fixture_type=ReplayFixtureType.BAD_DATA_CASES,
                instrument_id="BTCUSDT-PERP.BINANCE",
                timestamp_ns=[1000],
                anomaly_type="zero_price",
                description="Price is zero",
                extra_info=True,
            )


class TestStaleDataFixture:
    def test_valid_stale_data_fixture(self):
        f = StaleDataFixture(
            fixture_type=ReplayFixtureType.STALE_DATA_CASES,
            instrument_id="BTCUSDT-PERP.BINANCE",
            timestamp_ns=[1000],
            staleness_ms=5000,
            description="Order book not updated for 5s",
        )
        assert f.staleness_ms == 5000

    def test_stale_data_rejects_extra_fields(self):
        with pytest.raises(ValidationError):
            StaleDataFixture(
                fixture_type=ReplayFixtureType.STALE_DATA_CASES,
                instrument_id="BTCUSDT-PERP.BINANCE",
                timestamp_ns=[1000],
                staleness_ms=5000,
                description="test",
                invalid=True,
            )


# ---------------------------------------------------------------------------
# 4. BaseFixture shared constraints
# ---------------------------------------------------------------------------

class TestBaseFixtureConstraints:
    def test_empty_instrument_id_rejected(self):
        with pytest.raises(ValidationError):
            BarFixture(
                fixture_type=ReplayFixtureType.BARS,
                instrument_id="",
                timestamp_ns=[1000],
                open=[50000.0],
                high=[50100.0],
                low=[49900.0],
                close=[50100.0],
                volume=[10.0],
            )

    def test_default_seed_is_zero(self):
        f = BarFixture(
            fixture_type=ReplayFixtureType.BARS,
            instrument_id="BTCUSDT-PERP.BINANCE",
            timestamp_ns=[1000],
            open=[50000.0],
            high=[50100.0],
            low=[49900.0],
            close=[50100.0],
            volume=[10.0],
        )
        assert f.seed == 0

    def test_custom_seed_accepted(self):
        f = BarFixture(
            fixture_type=ReplayFixtureType.BARS,
            instrument_id="BTCUSDT-PERP.BINANCE",
            timestamp_ns=[1000],
            open=[50000.0],
            high=[50100.0],
            low=[49900.0],
            close=[50100.0],
            volume=[10.0],
            seed=42,
        )
        assert f.seed == 42


# ---------------------------------------------------------------------------
# 5. Deterministic hash
# ---------------------------------------------------------------------------

class TestDeterministicHash:
    def test_same_fixture_same_hash(self):
        kwargs = dict(
            fixture_type=ReplayFixtureType.BARS,
            instrument_id="BTCUSDT-PERP.BINANCE",
            timestamp_ns=[1000, 2000],
            open=[50000.0, 50100.0],
            high=[50100.0, 50200.0],
            low=[49900.0, 50000.0],
            close=[50100.0, 50200.0],
            volume=[10.0, 12.0],
        )
        f1 = BarFixture(**kwargs)
        f2 = BarFixture(**kwargs)
        assert compute_fixture_hash(f1) == compute_fixture_hash(f2)

    def test_different_fixture_different_hash(self):
        f1 = BarFixture(
            fixture_type=ReplayFixtureType.BARS,
            instrument_id="BTCUSDT-PERP.BINANCE",
            timestamp_ns=[1000],
            open=[50000.0],
            high=[50100.0],
            low=[49900.0],
            close=[50100.0],
            volume=[10.0],
        )
        f2 = BarFixture(
            fixture_type=ReplayFixtureType.BARS,
            instrument_id="BTCUSDT-PERP.BINANCE",
            timestamp_ns=[1000],
            open=[50000.0],
            high=[50100.0],
            low=[49900.0],
            close=[50200.0],  # different close
            volume=[10.0],
        )
        assert compute_fixture_hash(f1) != compute_fixture_hash(f2)

    def test_hash_is_sha256_hex(self):
        f = BarFixture(
            fixture_type=ReplayFixtureType.BARS,
            instrument_id="BTCUSDT-PERP.BINANCE",
            timestamp_ns=[1000],
            open=[50000.0],
            high=[50100.0],
            low=[49900.0],
            close=[50100.0],
            volume=[10.0],
        )
        h = compute_fixture_hash(f)
        assert len(h) == 64  # SHA-256 hex digest
        assert all(c in "0123456789abcdef" for c in h)


# ---------------------------------------------------------------------------
# 6. ReplayReportEvidence safety contract
# ---------------------------------------------------------------------------

class TestReplayReportEvidence:
    def _base_evidence(self, **overrides):
        defaults = dict(
            dataset_type=ReplayFixtureType.BARS,
            dataset_hash="abc123" * 10 + "ab",  # 64 chars
            row_count=1000,
            instrument_ids=["BTCUSDT-PERP.BINANCE"],
            time_range="2024-01-01:2024-03-01",
            bad_data_count=0,
            stale_data_count=0,
            missing_data_count=0,
            synthetic_data_used=True,
        )
        defaults.update(overrides)
        return defaults

    def test_valid_evidence(self):
        evidence = ReplayReportEvidence(**self._base_evidence())
        assert evidence.dataset_type == ReplayFixtureType.BARS
        assert evidence.credentials_used is False
        assert evidence.live_trading_enabled is False
        assert evidence.execution_authority is False

    def test_credentials_used_must_be_false(self):
        with pytest.raises(ValidationError):
            ReplayReportEvidence(**self._base_evidence(credentials_used=True))

    def test_execution_authority_must_be_false(self):
        with pytest.raises(ValidationError):
            ReplayReportEvidence(**self._base_evidence(execution_authority=True))

    def test_live_trading_enabled_must_be_false(self):
        with pytest.raises(ValidationError):
            ReplayReportEvidence(**self._base_evidence(live_trading_enabled=True))

    def test_bad_data_count_explicit_int_required(self):
        evidence = ReplayReportEvidence(**self._base_evidence(bad_data_count=5))
        assert evidence.bad_data_count == 5

    def test_missing_data_count_explicit_int_required(self):
        evidence = ReplayReportEvidence(**self._base_evidence(missing_data_count=3))
        assert evidence.missing_data_count == 3

    def test_stale_data_count_explicit_int_required(self):
        evidence = ReplayReportEvidence(**self._base_evidence(stale_data_count=2))
        assert evidence.stale_data_count == 2

    def test_evidence_rejects_extra_fields(self):
        with pytest.raises(ValidationError):
            ReplayReportEvidence(**self._base_evidence(secret_field="nope"))

    def test_evidence_with_all_dataset_types(self):
        for dt in ReplayFixtureType:
            evidence = ReplayReportEvidence(**self._base_evidence(dataset_type=dt))
            assert evidence.dataset_type == dt


# ---------------------------------------------------------------------------
# 7. Timestamp validation
# ---------------------------------------------------------------------------

class TestTimestampValidation:
    def test_monotonic_timestamps_accepted(self):
        f = BarFixture(
            fixture_type=ReplayFixtureType.BARS,
            instrument_id="BTCUSDT-PERP.BINANCE",
            timestamp_ns=[1000, 2000, 3000, 4000],
            open=[50000.0, 50100.0, 50200.0, 50300.0],
            high=[50100.0, 50200.0, 50300.0, 50400.0],
            low=[49900.0, 50000.0, 50100.0, 50200.0],
            close=[50100.0, 50200.0, 50300.0, 50400.0],
            volume=[10.0, 12.0, 8.0, 15.0],
        )
        assert len(f.timestamp_ns) == 4

    def test_out_of_order_timestamps_rejected(self):
        with pytest.raises(ValidationError):
            BarFixture(
                fixture_type=ReplayFixtureType.BARS,
                instrument_id="BTCUSDT-PERP.BINANCE",
                timestamp_ns=[3000, 1000, 2000],  # out of order
                open=[50000.0, 50100.0, 50200.0],
                high=[50100.0, 50200.0, 50300.0],
                low=[49900.0, 50000.0, 50100.0],
                close=[50100.0, 50200.0, 50300.0],
                volume=[10.0, 12.0, 8.0],
            )

    def test_duplicate_timestamps_rejected(self):
        with pytest.raises(ValidationError):
            BarFixture(
                fixture_type=ReplayFixtureType.BARS,
                instrument_id="BTCUSDT-PERP.BINANCE",
                timestamp_ns=[1000, 1000],  # duplicate
                open=[50000.0, 50100.0],
                high=[50100.0, 50200.0],
                low=[49900.0, 50000.0],
                close=[50100.0, 50200.0],
                volume=[10.0, 12.0],
            )


# ---------------------------------------------------------------------------
# 8. Backwards compatibility: existing tests still work
# ---------------------------------------------------------------------------

class TestBackwardsCompatibility:
    def test_original_replay_fixture_type_values_unchanged(self):
        """Existing 6 types must keep same string values."""
        expected = {
            "bars": ReplayFixtureType.BARS,
            "trades": ReplayFixtureType.TRADES,
            "quotes": ReplayFixtureType.QUOTES,
            "order_book_snapshots": ReplayFixtureType.ORDER_BOOK_SNAPSHOTS,
            "funding_rates": ReplayFixtureType.FUNDING_RATES,
            "liquidations": ReplayFixtureType.LIQUIDATIONS,
        }
        for value, member in expected.items():
            assert member.value == value

    def test_existing_replay_fixture_config_still_works(self):
        """ReplayFixtureConfig from original code must still validate."""
        from packages.backtest_runner.replay_fixtures import (
            ReplayFixtureConfig,
            validate_replay_fixture_config,
        )

        config = ReplayFixtureConfig(
            fixture_name="btcusdt_5m_normal",
            instrument_id="BTCUSDT-PERP.BINANCE",
            data_types=["bars", "trades", "quotes"],
            failure_modes=[],
        )
        validate_replay_fixture_config(config)  # must not raise
