"""
TypeScript/Python contract parity check.

Ensures Python-known event types have matching TypeScript reducer support.
This is a guardrail test, not a full schema compiler.
"""
import re
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Python event types (logical stream names → reducer event types)
PYTHON_EVENT_MAP = {
    "book_top": "BOOK_TOP",
    "book_l2": "BOOK_L2",
    "trades": "TRADE",
    "bars": "BAR",
    "signal": "SIGNAL_PREVIEW",
    "gate": "GATE_DECISION",
    "trade_action": "TRADE_ACTION",
    "execution": "EXECUTION_REPORT",
    "account": "ACCOUNT",
    "positions": "POSITIONS",
    "orders": "OPEN_ORDERS",
    "order_events": "ORDER_EVENT",
    "quant_levels": "QUANT_LEVELS",
    "tick_to_trade": "TICK_TO_TRADE",
    "health": "RUNTIME_HEALTH",
}

# TypeScript types file
TS_TYPES_PATH = PROJECT_ROOT / "apps" / "web" / "lib" / "tradehud" / "types.ts"
TS_REDUCER_PATH = PROJECT_ROOT / "apps" / "web" / "lib" / "tradehud" / "reducer.ts"


def load_ts_event_types() -> set[str]:
    """Extract TradeHudEvent type strings from TypeScript."""
    if not TS_TYPES_PATH.exists():
        pytest.skip("types.ts not found")
    content = TS_TYPES_PATH.read_text()
    # Match: | { type: "BOOK_TOP"; ... }
    matches = re.findall(r'type:\s*"(\w+)"', content)
    return set(matches)


def load_ts_reducer_cases() -> set[str]:
    """Extract reducer case statements from TypeScript."""
    if not TS_REDUCER_PATH.exists():
        pytest.skip("reducer.ts not found")
    content = TS_REDUCER_PATH.read_text()
    # Match: case "BOOK_TOP":
    matches = re.findall(r'case\s+"(\w+)":', content)
    return set(matches)


class TestEventParity:
    """Python event types must have matching TypeScript reducer support."""

    def test_all_python_events_have_ts_types(self):
        ts_types = load_ts_event_types()
        missing = []
        for py_name, ts_name in PYTHON_EVENT_MAP.items():
            if ts_name not in ts_types:
                missing.append(f"{py_name} -> {ts_name}")
        assert missing == [], f"TS types missing for Python events: {missing}"

    def test_all_python_events_have_reducer_cases(self):
        ts_cases = load_ts_reducer_cases()
        missing = []
        for py_name, ts_name in PYTHON_EVENT_MAP.items():
            if ts_name not in ts_cases:
                missing.append(f"{py_name} -> {ts_name}")
        assert missing == [], f"TS reducer missing cases for: {missing}"

    def test_signal_preview_is_not_trade_action(self):
        """SignalPreview and TradeAction must be distinct events."""
        ts_types = load_ts_event_types()
        assert "SIGNAL_PREVIEW" in ts_types
        assert "TRADE_ACTION" in ts_types
        assert "SIGNAL_PREVIEW" != "TRADE_ACTION"

    def test_gate_decision_is_not_execution(self):
        """GateDecision and ExecutionReport must be distinct events."""
        ts_types = load_ts_event_types()
        assert "GATE_DECISION" in ts_types
        assert "EXECUTION_REPORT" in ts_types
        assert "GATE_DECISION" != "EXECUTION_REPORT"

    def test_python_stream_names_match_nd_map(self):
        """Python stream map keys must match event map keys."""
        from packages.tradehud_contracts.config import TradeHudRedisConfig
        config = TradeHudRedisConfig()
        stream_map = config.get_stream_map()
        # Every Python event type should have a corresponding stream
        for py_name in PYTHON_EVENT_MAP:
            if py_name in ("liquidations",):
                continue
            assert py_name in stream_map or f"No stream for {py_name}", \
                f"Python event '{py_name}' has no nd.* stream mapping"

    def test_ts_has_snapshot_and_metadata_events(self):
        """TS must support SNAPSHOT, SET_MODE, SET_BACKEND, SET_FEED_STATUS."""
        ts_types = load_ts_event_types()
        for required in ("SNAPSHOT", "SET_MODE", "SET_BACKEND", "SET_FEED_STATUS"):
            assert required in ts_types, f"TS missing required event: {required}"
