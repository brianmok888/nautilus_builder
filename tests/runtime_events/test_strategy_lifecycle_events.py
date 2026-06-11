"""Runtime event lineage tests — Segment 13."""
from packages.runtime_events.event_types import RuntimeEventType


class TestRuntimeEventTypes:
    def test_all_required_events_defined(self) -> None:
        required = [
            "STRATEGY_CREATED", "STRATEGY_VALIDATED", "STRATEGY_COMPILED",
            "BACKTEST_REQUESTED", "BACKTEST_COMPLETED", "BACKTEST_FAILED",
            "EVIDENCE_REGISTERED", "EVIDENCE_VERIFIED",
            "PROMOTION_REQUESTED", "PROMOTION_BLOCKED", "PROMOTION_REJECTED",
        ]
        for name in required:
            assert hasattr(RuntimeEventType, name), f"Missing RuntimeEventType.{name}"

    def test_event_type_values(self) -> None:
        assert RuntimeEventType.STRATEGY_CREATED.value == "strategy.created"
        assert RuntimeEventType.BACKTEST_COMPLETED.value == "backtest.completed"
        assert RuntimeEventType.PROMOTION_BLOCKED.value == "promotion.blocked"

    def test_no_live_execution_events(self) -> None:
        """Builder must not define live execution events."""
        values = [e.value for e in RuntimeEventType]
        assert not any("order" in v for v in values), "Live order events must not exist in Builder"
        assert not any("submit" in v for v in values), "Submit events must not exist in Builder"
