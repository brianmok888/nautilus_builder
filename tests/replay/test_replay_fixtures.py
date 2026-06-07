"""Tests for replay fixture types beyond synthetic quote ticks."""
from __future__ import annotations

import pytest

from packages.backtest_runner.replay_fixtures import (
    ReplayFixtureType,
    FailureModeFixture,
    ReplayFixtureConfig,
    validate_replay_fixture_config,
)


class TestReplayFixtureType:
    def test_all_types_exist(self):
        assert ReplayFixtureType.BARS.value == "bars"
        assert ReplayFixtureType.TRADES.value == "trades"
        assert ReplayFixtureType.QUOTES.value == "quotes"
        assert ReplayFixtureType.ORDER_BOOK_SNAPSHOTS.value == "order_book_snapshots"
        assert ReplayFixtureType.FUNDING_RATES.value == "funding_rates"
        assert ReplayFixtureType.LIQUIDATIONS.value == "liquidations"


class TestFailureModeFixture:
    def test_failure_modes_exist(self):
        modes = [
            "missing_bars",
            "stale_trades",
            "crossed_book",
            "wide_spread",
            "zero_price",
            "negative_size",
            "out_of_order_timestamps",
            "duplicate_events",
        ]
        for mode in modes:
            fixture = FailureModeFixture(mode=mode, description=f"Test {mode}")
            assert fixture.mode == mode

    def test_failure_mode_has_description(self):
        fixture = FailureModeFixture(mode="missing_bars", description="Bars are missing from dataset")
        assert len(fixture.description) > 0


class TestReplayFixtureConfig:
    def test_basic_config_validates(self):
        config = ReplayFixtureConfig(
            fixture_name="btcusdt_5m_normal",
            instrument_id="BTCUSDT-PERP.BINANCE",
            data_types=["bars", "trades", "quotes"],
            failure_modes=[],
        )
        assert config.fixture_name == "btcusdt_5m_normal"
        assert len(config.data_types) == 3

    def test_config_with_failure_modes(self):
        config = ReplayFixtureConfig(
            fixture_name="btcusdt_5m_crossed_book",
            instrument_id="BTCUSDT-PERP.BINANCE",
            data_types=["bars", "quotes", "order_book_snapshots"],
            failure_modes=[
                FailureModeFixture(mode="crossed_book", description="Bid > Ask"),
            ],
        )
        assert len(config.failure_modes) == 1

    def test_config_requires_at_least_one_data_type(self):
        with pytest.raises(Exception):
            ReplayFixtureConfig(
                fixture_name="empty",
                instrument_id="BTCUSDT-PERP.BINANCE",
                data_types=[],
                failure_modes=[],
            )


class TestReplayFixtureConfigValidation:
    def test_valid_config_passes(self):
        config = ReplayFixtureConfig(
            fixture_name="ethusdt_15m_funding_stress",
            instrument_id="ETHUSDT-PERP.BINANCE",
            data_types=["bars", "funding_rates", "liquidations"],
            failure_modes=[],
        )
        validate_replay_fixture_config(config)  # should not raise

    def test_unknown_instrument_format_rejected(self):
        config = ReplayFixtureConfig(
            fixture_name="test",
            instrument_id="",  # empty instrument_id
            data_types=["bars"],
            failure_modes=[],
        )
        with pytest.raises(Exception):
            validate_replay_fixture_config(config)
