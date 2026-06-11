"""Builder metrics counters — tracked for observability."""
from __future__ import annotations

from collections import defaultdict


class BuilderMetrics:
    """In-memory metrics counters for Builder observability."""

    def __init__(self) -> None:
        self._counters: dict[str, int] = defaultdict(int)

    def increment(self, metric: str, value: int = 1) -> None:
        self._counters[metric] += value

    def get(self, metric: str) -> int:
        return self._counters.get(metric, 0)

    def snapshot(self) -> dict[str, int]:
        return dict(self._counters)

    def reset(self) -> None:
        self._counters.clear()


# Canonical metric names
METRIC_NAMES = {
    "builder_validation_total",
    "builder_validation_failed_total",
    "builder_compile_total",
    "builder_compile_failed_total",
    "builder_backtest_total",
    "builder_evidence_verify_total",
    "builder_promotion_blocked_total",
    "builder_forbidden_authority_scan_status",
}
