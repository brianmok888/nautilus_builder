"""Tests for data alignment checks."""
from __future__ import annotations

from packages.catalog_datasets.data_alignment import (
    check_alignment,
    check_for_lookahead,
    check_staleness,
)


class TestAlignment:
    def test_monotonic_timestamps_pass(self):
        records = [
            {"ts": 1000, "value": 1.0},
            {"ts": 2000, "value": 2.0},
            {"ts": 3000, "value": 3.0},
        ]
        issues = check_alignment(records)
        assert len(issues) == 0

    def test_non_monotonic_timestamps_fail(self):
        records = [
            {"ts": 3000, "value": 3.0},
            {"ts": 1000, "value": 1.0},
            {"ts": 2000, "value": 2.0},
        ]
        issues = check_alignment(records)
        assert len(issues) > 0
        assert any(i.check == "timestamp_monotonicity" for i in issues)

    def test_missing_timestamp_fails(self):
        records = [
            {"value": 1.0},
            {"ts": 2000, "value": 2.0},
        ]
        issues = check_alignment(records)
        assert any(i.check == "missing_timestamp" for i in issues)

    def test_empty_records_pass(self):
        assert check_alignment([]) == []
        assert check_alignment([{"ts": 1}]) == []

    def test_ts_event_field_recognized(self):
        records = [
            {"ts_event": 1000},
            {"ts_event": 2000},
        ]
        issues = check_alignment(records)
        assert len(issues) == 0


class TestLookahead:
    def test_no_lookahead_passes(self):
        bars = [{"ts": 1000}]
        trades = [{"ts": 1500}]
        issues = check_for_lookahead(bars, trades)
        assert len(issues) == 0

    def test_lookahead_detected(self):
        bars = [{"ts": 2000}]
        trades = [{"ts": 1000}]
        issues = check_for_lookahead(bars, trades)
        assert any(i.check == "lookahead_leakage" for i in issues)

    def test_empty_data_passes(self):
        assert check_for_lookahead([], []) == []


class TestStaleness:
    def test_fresh_data_passes(self):
        records = [{"age_ms": 100, "value": 1.0}]
        issues = check_staleness(records, max_age_ms=1000)
        assert len(issues) == 0

    def test_stale_data_warns(self):
        records = [{"source_age_ms": 5000, "value": 1.0}]
        issues = check_staleness(records, max_age_ms=1000)
        assert any(i.check == "source_staleness" for i in issues)
