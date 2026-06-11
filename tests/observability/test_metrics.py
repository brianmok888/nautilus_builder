"""Tests for Builder metrics."""
from __future__ import annotations

from packages.observability.metrics import BuilderMetrics, METRIC_NAMES


class TestBuilderMetrics:
    def test_increment_and_get(self):
        m = BuilderMetrics()
        m.increment("builder_validation_total")
        assert m.get("builder_validation_total") == 1

    def test_increment_by_value(self):
        m = BuilderMetrics()
        m.increment("builder_backtest_total", 5)
        assert m.get("builder_backtest_total") == 5

    def test_unknown_metric_returns_zero(self):
        m = BuilderMetrics()
        assert m.get("nonexistent") == 0

    def test_snapshot(self):
        m = BuilderMetrics()
        m.increment("builder_validation_total")
        m.increment("builder_compile_total", 3)
        snap = m.snapshot()
        assert snap["builder_validation_total"] == 1
        assert snap["builder_compile_total"] == 3

    def test_reset(self):
        m = BuilderMetrics()
        m.increment("builder_validation_total")
        m.reset()
        assert m.get("builder_validation_total") == 0

    def test_metric_names_cover_spec(self):
        expected = {
            "builder_validation_total",
            "builder_compile_total",
            "builder_backtest_total",
            "builder_evidence_verify_total",
            "builder_promotion_blocked_total",
            "builder_forbidden_authority_scan_status",
        }
        assert expected.issubset(METRIC_NAMES)
