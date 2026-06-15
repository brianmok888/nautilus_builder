"""
ND freshness and missing-value contract tests.

Verifies all SourceStatus values, missing != true_zero, and freshness tracking.
"""
import json
import time
from pathlib import Path

import pytest
from packages.tradehud_contracts.normalizer import (
    to_optional_float,
    to_optional_int,
    is_explicit_zero,
)
from packages.tradehud_contracts.config import TradeHudRedisConfig
from packages.tradehud_contracts.stream_health import StreamHealthTracker

TS = 1700000000_000000000


class TestMissingNotZero:
    """Missing values must not become zero."""

    def test_missing_price_not_zero(self):
        result = to_optional_float(None)
        assert result is None
        assert result != 0.0

    def test_missing_qty_not_zero(self):
        result = to_optional_float("")
        assert result is None
        assert result != 0.0

    def test_missing_ts_not_zero(self):
        result = to_optional_int(None)
        assert result is None
        assert result != 0

    def test_explicit_zero_stays_zero(self):
        result = to_optional_float("0")
        assert result == 0.0

    def test_explicit_int_zero_stays_zero(self):
        result = to_optional_int("0")
        assert result == 0

    def test_missing_distinct_from_true_zero(self):
        missing = to_optional_float(None)
        zero = to_optional_float("0")
        assert missing is None
        assert zero == 0.0
        assert is_explicit_zero(zero) is True
        assert is_explicit_zero(missing) is False


class TestSourceStatusValues:
    """All seven source_status values must be valid."""

    VALID_STATUSES = [
        "live", "stale", "missing", "synthetic", "true_zero", "unavailable", "unknown"
    ]

    def test_all_statuses_defined(self):
        from packages.tradehud_contracts.models import SourceStatus
        # SourceStatus is a Literal — check all values appear in the type
        import typing
        args = typing.get_args(SourceStatus)
        for status in self.VALID_STATUSES:
            assert status in args, f"{status} must be in SourceStatus"

    def test_fresh_record_is_live(self):
        config = TradeHudRedisConfig()
        tracker = StreamHealthTracker(config)
        tracker.mark_connected(True)
        now_ns = int(time.time() * 1_000_000_000)
        tracker.record_event("book_top", "1-0", now_ns)
        tracker.evaluate()
        status = tracker.get_stream_status("book_top")
        assert status == "live"

    def test_old_record_is_stale(self):
        config = TradeHudRedisConfig(stream_stale_ms=1000)
        tracker = StreamHealthTracker(config)
        tracker.mark_connected(True)
        old_ns = int((time.time() - 100) * 1_000_000_000)
        tracker.record_event("book_top", "1-0", old_ns)
        tracker.evaluate()
        status = tracker.get_stream_status("book_top")
        assert status == "stale"

    def test_unseen_stream_is_missing(self):
        config = TradeHudRedisConfig()
        tracker = StreamHealthTracker(config)
        tracker.mark_connected(True)
        tracker.evaluate()
        status = tracker.get_stream_status("bars")
        assert status in ("missing", "unknown")


class TestTrueZeroVsMissing:
    """Explicit zero liquidation count (true_zero) is distinct from missing."""

    def test_no_liquidation_events_is_true_zero(self):
        # When source is live but liquidation count is 0 → true_zero
        zero_val = to_optional_int("0")
        assert zero_val == 0
        assert is_explicit_zero(zero_val) is True

    def test_no_liquidation_stream_is_missing(self):
        # When stream not connected → missing/unavailable
        missing_val = to_optional_int(None)
        assert missing_val is None
        assert is_explicit_zero(missing_val) is False


class TestStaleFreshness:
    def test_stale_threshold(self):
        config = TradeHudRedisConfig(stream_stale_ms=5000)
        tracker = StreamHealthTracker(config)
        tracker.mark_connected(True)
        recent_ns = int(time.time() * 1_000_000_000)
        tracker.record_event("trades", "1-0", recent_ns)
        tracker.evaluate()
        status = tracker.get_stream_status("trades")
        assert status == "live"

    def test_stale_after_threshold(self):
        config = TradeHudRedisConfig(stream_stale_ms=1000)
        tracker = StreamHealthTracker(config)
        tracker.mark_connected(True)
        old_ns = int((time.time() - 10) * 1_000_000_000)
        tracker.record_event("trades", "1-0", old_ns)
        tracker.evaluate()
        status = tracker.get_stream_status("trades")
        assert status == "stale"
