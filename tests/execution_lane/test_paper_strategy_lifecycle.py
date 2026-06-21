"""TDD tests for ExecutionLanePaperStrategy lifecycle fixes.

Covers:
- M-01: Bar subscription support (currently only subscribes to quote_ticks)
- M-02: on_reset cleanup (currently missing)
- L-03: on_stop explicit unsubscribe (currently missing)

Uses PropertyMock for NT Cython read-only properties (cache, etc).
"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch, PropertyMock

from nautilus_trader.model.identifiers import InstrumentId

from packages.execution_lane.paper_strategy import (
    ExecutionLanePaperStrategy,
    ExecutionLanePaperStrategyConfig,
)


def _make_config(**overrides):
    defaults = dict(
        instrument_id=InstrumentId.from_str("BTCUSDT-PERP.BINANCE"),
        strategy_lineage_id="lineage-001",
        strategy_version_id="v1",
        runtime_profile_id="profile-001",
    )
    defaults.update(overrides)
    return ExecutionLanePaperStrategyConfig(**defaults)


def _make_strategy(config=None):
    if config is None:
        config = _make_config()
    return ExecutionLanePaperStrategy(config)


# ---------------------------------------------------------------------------
# M-02: on_reset cleanup
# ---------------------------------------------------------------------------


class TestOnReset:
    def test_on_reset_clears_observed_tick_count(self):
        strategy = _make_strategy()
        strategy.observed_quote_ticks = 42
        strategy.on_reset()
        assert strategy.observed_quote_ticks == 0

    def test_on_reset_clears_instrument(self):
        strategy = _make_strategy()
        strategy.instrument = MagicMock(name="mock_instrument")
        strategy.on_reset()
        assert strategy.instrument is None

    def test_on_reset_clears_observed_bars(self):
        strategy = _make_strategy()
        strategy.observed_bars = 99
        strategy.on_reset()
        assert strategy.observed_bars == 0


# ---------------------------------------------------------------------------
# L-03: on_stop explicit unsubscribe
# ---------------------------------------------------------------------------


class TestOnStop:
    def test_on_stop_calls_unsubscribe_quote_ticks_by_default(self):
        strategy = _make_strategy()
        with patch.object(strategy, "unsubscribe_quote_ticks") as mock_unsub:
            strategy.on_stop()
            mock_unsub.assert_called_once_with(
                instrument_id=strategy.config.instrument_id,
            )

    def test_on_stop_with_bar_type_calls_unsubscribe_bars(self):
        config = _make_config(bar_type="BTCUSDT-PERP.BINANCE-5-MINUTE-LAST-EXTERNAL")
        strategy = _make_strategy(config)
        with patch.object(strategy, "unsubscribe_bars") as mock_unsub_bars, \
             patch.object(strategy, "unsubscribe_quote_ticks") as mock_unsub_ticks:
            strategy.on_stop()
            mock_unsub_bars.assert_called_once_with(bar_type=config.bar_type)
            mock_unsub_ticks.assert_not_called()


# ---------------------------------------------------------------------------
# M-01: Bar subscription support
# ---------------------------------------------------------------------------


class TestOnStartBarSubscription:
    def _patch_cache(self, strategy, instrument_return_value):
        """Patch the cache property to return a mock with controlled instrument()."""
        mock_cache = MagicMock()
        mock_cache.instrument.return_value = instrument_return_value
        return patch.object(type(strategy), "cache", new_callable=PropertyMock, return_value=mock_cache)

    def test_on_start_subscribes_quote_ticks_when_no_bar_type(self):
        strategy = _make_strategy()
        with self._patch_cache(strategy, MagicMock()), \
             patch.object(strategy, "subscribe_quote_ticks") as mock_sub:
            strategy.on_start()
            mock_sub.assert_called_once_with(
                instrument_id=strategy.config.instrument_id,
            )

    def test_on_start_with_bar_type_subscribes_bars(self):
        config = _make_config(bar_type="BTCUSDT-PERP.BINANCE-5-MINUTE-LAST-EXTERNAL")
        strategy = _make_strategy(config)
        with self._patch_cache(strategy, MagicMock()), \
             patch.object(strategy, "request_bars") as mock_req_bars, \
             patch.object(strategy, "subscribe_bars") as mock_sub_bars, \
             patch.object(strategy, "subscribe_quote_ticks") as mock_sub_ticks:
            strategy.on_start()
            # Warmup: request_bars is called before subscribe_bars (P2-7).
            mock_req_bars.assert_called_once_with(bar_type=config.bar_type)
            mock_sub_bars.assert_called_once_with(bar_type=config.bar_type)
            mock_sub_ticks.assert_not_called()

    def test_on_start_does_not_subscribe_when_instrument_missing(self):
        strategy = _make_strategy()
        with self._patch_cache(strategy, None), \
             patch.object(strategy, "subscribe_quote_ticks") as mock_sub:
            strategy.on_start()
            mock_sub.assert_not_called()


# ---------------------------------------------------------------------------
# Bar counting
# ---------------------------------------------------------------------------


class TestOnBar:
    def test_on_bar_increments_counter(self):
        strategy = _make_strategy()
        mock_bar = MagicMock()
        strategy.on_bar(mock_bar)
        assert strategy.observed_bars == 1
        strategy.on_bar(mock_bar)
        assert strategy.observed_bars == 2
