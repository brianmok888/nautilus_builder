"""
ND Redis adapter contract tests.

Verifies parser correctness, missing-field rejection, and read-only behavior
without requiring a real Redis server.
"""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from packages.tradehud_contracts.redis_adapter import (
    parse_stream_entry,
    build_snapshot_from_redis,
    _parse_book_top,
    _parse_book_l2,
    _parse_trade,
    _parse_account,
    _parse_positions,
    _parse_open_orders,
    _parse_signal,
    _parse_gate,
    _parse_trade_action,
    _parse_execution,
    _parse_quant_levels,
    _parse_tick_to_trade,
    _parse_runtime_health,
)
from packages.tradehud_contracts.config import TradeHudRedisConfig

TS = 1700000000_000000000


class TestBookTopParser:
    def test_valid_book_top(self):
        data = {
            "symbol": "BTCUSDT-PERP", "bid_price": "50000", "ask_price": "50001",
            "bid_size": "1.5", "ask_size": "2.0", "ts_event_ns": str(TS),
        }
        result = _parse_book_top(data)
        assert result is not None
        assert result.symbol == "BTCUSDT-PERP"
        assert result.bid_price == 50000.0
        assert result.ask_price == 50001.0

    def test_missing_price_returns_none(self):
        data = {"symbol": "BTCUSDT-PERP", "ts_event_ns": str(TS)}
        result = _parse_book_top(data)
        assert result is None

    def test_missing_size_is_none_not_zero(self):
        data = {
            "symbol": "BTCUSDT-PERP", "bid_price": "50000", "ask_price": "50001",
            "ts_event_ns": str(TS),
        }
        result = _parse_book_top(data)
        assert result is not None
        assert result.bid_size is None
        assert result.ask_size is None

    def test_explicit_zero_size_stays_zero(self):
        data = {
            "symbol": "BTCUSDT-PERP", "bid_price": "50000", "ask_price": "50001",
            "bid_size": "0", "ask_size": "0", "ts_event_ns": str(TS),
        }
        result = _parse_book_top(data)
        assert result is not None
        assert result.bid_size == 0.0
        assert result.ask_size == 0.0


class TestTradeParser:
    def test_valid_trade(self):
        data = {
            "symbol": "BTCUSDT-PERP", "price": "50000.5", "qty": "0.5",
            "side": "buy", "trade_id": "t1", "ts_event_ns": str(TS),
        }
        result = _parse_trade(data)
        assert result is not None
        assert result.price == 50000.5
        assert result.qty == 0.5

    def test_missing_price_returns_none(self):
        data = {"symbol": "BTC", "qty": "0.5", "ts_event_ns": str(TS), "side": "buy", "trade_id": "t1"}
        assert _parse_trade(data) is None

    def test_missing_qty_returns_none(self):
        data = {"symbol": "BTC", "price": "50000", "ts_event_ns": str(TS), "side": "buy", "trade_id": "t1"}
        assert _parse_trade(data) is None

    def test_missing_ts_returns_none(self):
        data = {"symbol": "BTC", "price": "50000", "qty": "0.5", "side": "buy", "trade_id": "t1"}
        assert _parse_trade(data) is None

    def test_explicit_zero_qty_stays_zero(self):
        data = {
            "symbol": "BTCUSDT-PERP", "price": "50000", "qty": "0",
            "side": "sell", "trade_id": "z1", "ts_event_ns": str(TS),
        }
        result = _parse_trade(data)
        assert result is not None
        assert result.qty == 0.0


class TestL2Parser:
    def test_valid_l2(self):
        data = {
            "symbol": "BTCUSDT-PERP",
            "bids": [{"price": 50000, "size": 1.5}],
            "asks": [{"price": 50001, "size": 2.0}],
            "spread": "1.0", "ts_event_ns": str(TS),
        }
        result = _parse_book_l2(data)
        assert result is not None
        assert len(result.bids) == 1
        assert result.bids[0].price == 50000.0

    def test_missing_levels_returns_none(self):
        data = {"symbol": "BTC", "spread": "1.0", "ts_event_ns": str(TS)}
        result = _parse_book_l2(data)
        assert result is None


class TestSignalParser:
    def test_valid_signal(self):
        data = {
            "signal_id": "s1", "symbol": "BTCUSDT-PERP",
            "feature_hash": "fh", "context_hash": "ch",
            "policy_hash": "ph", "graph_trace_hash": "gth",
            "confidence_score": "0.75", "direction": "long",
            "ts_event_ns": str(TS),
        }
        result = _parse_signal(data)
        assert result is not None
        assert result.direction == "long"
        assert result.confidence_score == 0.75


class TestGateParser:
    def test_approved_gate(self):
        data = {
            "decision_id": "g1", "decision": "APPROVED",
            "reason_code": "ALL_GATES_PASSED",
            "gate_decision_hash": "gdh1", "source_signal_hash": "fh",
            "ts_event_ns": str(TS),
        }
        result = _parse_gate(data)
        assert result is not None
        assert result.decision == "APPROVED"

    def test_rejected_gate_has_blocking(self):
        data = {
            "decision_id": "g2", "decision": "REJECTED",
            "first_blocking_gate": "RISK_LIMIT",
            "reason_code": "MAX_SIZE",
            "gate_decision_hash": "gdh2", "source_signal_hash": "fh",
            "ts_event_ns": str(TS),
        }
        result = _parse_gate(data)
        assert result is not None
        assert result.first_blocking_gate == "RISK_LIMIT"

    def test_hold_gate(self):
        data = {
            "decision_id": "g3", "decision": "HOLD",
            "reason_code": "AWAITING",
            "gate_decision_hash": "gdh3", "source_signal_hash": "fh",
            "ts_event_ns": str(TS),
        }
        result = _parse_gate(data)
        assert result is not None
        assert result.decision == "HOLD"


class TestTradeActionParser:
    def test_valid_trade_action(self):
        data = {
            "action_id": "a1", "action": "OPEN_LONG", "side": "buy",
            "price": "50001", "qty": "0.5",
            "trade_action_hash": "tah1", "source_gate_decision_hash": "gdh1",
            "ts_event_ns": str(TS),
        }
        result = _parse_trade_action(data)
        assert result is not None
        assert result.action == "OPEN_LONG"
        assert result.created_by == "run_gate_engine"

    def test_missing_trade_action_hash_rejects(self):
        """Missing trade_action_hash must reject (return None).
        trade_action_hash is a required provenance field."""
        data = {
            "action_id": "a1", "action": "OPEN_LONG", "side": "buy",
            "price": "50001", "qty": "0.5",
            "source_gate_decision_hash": "gdh1", "ts_event_ns": str(TS),
        }
        assert _parse_trade_action(data) is None

    def test_missing_source_gate_decision_hash_rejects(self):
        """Missing source_gate_decision_hash must also reject."""
        data = {
            "action_id": "a1", "action": "OPEN_LONG", "side": "buy",
            "price": "50001", "qty": "0.5",
            "trade_action_hash": "tah1", "ts_event_ns": str(TS),
        }
        assert _parse_trade_action(data) is None


class TestExecutionParser:
    def test_filled_execution(self):
        data = {
            "report_id": "e1", "status": "FILLED",
            "client_order_id": "cl1", "trade_action_hash": "tah1",
            "symbol": "BTCUSDT-PERP", "side": "buy",
            "submit_ts_ns": str(TS), "ts_event_ns": str(TS),
        }
        result = _parse_execution(data)
        assert result is not None
        assert result.status == "FILLED"

    def test_rejected_execution_has_reason(self):
        data = {
            "report_id": "e2", "status": "REJECTED",
            "client_order_id": "cl2", "trade_action_hash": "tah2",
            "symbol": "ETHUSDT-PERP", "side": "sell",
            "rejection_reason": "INSUFFICIENT_MARGIN",
            "submit_ts_ns": str(TS), "ts_event_ns": str(TS),
        }
        result = _parse_execution(data)
        assert result is not None
        assert result.rejection_reason == "INSUFFICIENT_MARGIN"


class TestParseStreamEntry:
    def test_parse_book_top_entry(self):
        fields = {
            b"symbol": b"BTCUSDT-PERP", b"bid_price": b"50000",
            b"ask_price": b"50001", b"ts_event_ns": str(TS).encode(),
        }
        result = parse_stream_entry("book_top", fields)
        assert result is not None
        field_name, model = result
        assert field_name == "book_top"
        assert model.symbol == "BTCUSDT-PERP"

    def test_unknown_stream_returns_none(self):
        result = parse_stream_entry("nonexistent", {})
        assert result is None


class TestBuildSnapshot:
    def test_build_snapshot_from_entries(self):
        entries = {
            "book_top": {
                b"symbol": b"BTCUSDT-PERP", b"bid_price": b"50000",
                b"ask_price": b"50001", b"ts_event_ns": str(TS).encode(),
            },
        }
        snapshot = build_snapshot_from_redis(entries)
        assert snapshot.book_top is not None
        assert snapshot.book_top.symbol == "BTCUSDT-PERP"

    def test_empty_entries_produces_empty_snapshot(self):
        snapshot = build_snapshot_from_redis({})
        assert snapshot.book_top is None
        assert snapshot.latest_signal_preview is None


class TestAdapterReadOnly:
    """Redis adapter must be read-only — no XADD, DEL, SET, PUBLISH."""

    def test_no_xadd_in_source(self):
        import packages.tradehud_contracts.redis_adapter as mod
        import re
        raw = open(mod.__file__).read()
        # Strip docstrings and comments
        source = re.sub(r'""".*?"""', '', raw, flags=re.DOTALL)
        source = re.sub(r"#.*$", "", source, flags=re.MULTILINE)
        source = source.lower()
        assert "xadd" not in source, "Adapter must not contain XADD"
        assert "xdel" not in source, "Adapter must not contain XDEL"
        assert "xset" not in source, "Adapter must not contain XSET"

    def test_no_publish_in_source(self):
        import packages.tradehud_contracts.redis_adapter as mod
        import re
        raw = open(mod.__file__).read()
        source = re.sub(r'""".*?"""', '', raw, flags=re.DOTALL)
        source = re.sub(r"#.*$", "", source, flags=re.MULTILINE)
        source = source.lower()
        assert ".publish(" not in source, "Adapter must not call PUBLISH"

    def test_no_set_in_source(self):
        import packages.tradehud_contracts.redis_adapter as mod
        source = open(mod.__file__).read()
        # Check for redis SET command (not Python set() or assignment)
        for line in source.split("\n"):
            stripped = line.strip()
            if stripped.startswith("#") or stripped.startswith('"') or stripped.startswith("'"):
                continue
            if "\"set\"" in line.lower() or "'set'" in line.lower() or ".set(" in line:
                assert "set" not in line.lower().replace("offset", "").replace("setdefault", ""), \
                    f"Suspicious SET in adapter: {line}"

    def test_only_read_commands_used(self):
        import packages.tradehud_contracts.redis_adapter as mod
        import re
        raw = open(mod.__file__).read()
        source = re.sub(r'""".*?"""', '', raw, flags=re.DOTALL)
        source = re.sub(r"#.*$", "", source, flags=re.MULTILINE)
        source = source.lower()
        assert "xread" in source, "Adapter should use XREAD"
        forbidden = [".xadd(", ".xdel(", ".xtrim(", ".publish(", "flushdb", "flushall", ".eval("]
        for cmd in forbidden:
            assert cmd not in source, f"Forbidden Redis command in adapter: {cmd}"


class TestOpenOrdersParser:
    """Tests for _parse_open_orders - open_orders parsing (legacy/unsupported in ND)."""

    def test_valid_order_snapshot(self):
        """Valid open_orders record parses correctly."""
        data = {
            "orders": [
                {
                    "order_id": "ord-001",
                    "client_order_id": "coid-001",
                    "symbol": "BTCUSDT-PERP",
                    "venue": "BINANCE",
                    "side": "buy",
                    "order_type": "LIMIT",
                    "price": "50000",
                    "qty": "1.5",
                    "filled_qty": "0.3",
                    "status": "PARTIAL_FILL",
                    "ts_event_ns": str(TS),
                }
            ]
        }
        result = _parse_open_orders(data)
        assert len(result) == 1
        o = result[0]
        assert o.order_id == "ord-001"
        assert o.client_order_id == "coid-001"
        assert o.symbol == "BTCUSDT-PERP"
        assert o.venue == "BINANCE"
        assert o.side == "buy"
        assert o.order_type == "LIMIT"
        assert o.price == 50000.0
        assert o.qty == 1.5
        assert o.filled_qty == 0.3
        assert o.status == "PARTIAL_FILL"
        assert o.source_status == "live"
        assert o.provenance == "redis"

    def test_multiple_orders(self):
        """Multiple orders in a snapshot all parse."""
        data = {
            "orders": [
                {"order_id": "o1", "price": "50000", "qty": "1.0", "ts_event_ns": str(TS)},
                {"order_id": "o2", "price": "50100", "qty": "0.5", "ts_event_ns": str(TS)},
            ]
        }
        result = _parse_open_orders(data)
        assert len(result) == 2
        assert result[0].order_id == "o1"
        assert result[1].order_id == "o2"

    def test_single_order_as_dict(self):
        """Single order as a dict (not list) parses."""
        data = {
            "order_id": "o-single",
            "price": "50000",
            "qty": "1.0",
            "ts_event_ns": str(TS),
        }
        result = _parse_open_orders(data)
        assert len(result) == 1
        assert result[0].order_id == "o-single"

    def test_missing_qty_does_not_become_zero(self):
        """Order with missing qty must be skipped, NOT silently become 0."""
        data = {
            "orders": [
                {
                    "order_id": "no-qty-order",
                    "price": "50000",
                    "ts_event_ns": str(TS),
                }
            ]
        }
        result = _parse_open_orders(data)
        assert len(result) == 0, "Missing qty must reject the order, not default to 0"

    def test_missing_qty_does_not_become_zero_partial(self):
        """Valid order + missing-qty order: only valid one survives."""
        data = {
            "orders": [
                {"order_id": "good", "price": "50000", "qty": "1.0", "ts_event_ns": str(TS)},
                {"order_id": "no-qty", "price": "50100", "ts_event_ns": str(TS)},
            ]
        }
        result = _parse_open_orders(data)
        assert len(result) == 1
        assert result[0].order_id == "good"

    def test_missing_price_skips(self):
        """Order with missing price is skipped."""
        data = {
            "orders": [
                {"order_id": "no-price", "qty": "1.0", "ts_event_ns": str(TS)},
            ]
        }
        result = _parse_open_orders(data)
        assert len(result) == 0

    def test_missing_ts_skips(self):
        """Order with missing ts is skipped."""
        data = {
            "orders": [
                {"order_id": "no-ts", "price": "50000", "qty": "1.0"},
            ]
        }
        result = _parse_open_orders(data)
        assert len(result) == 0

    def test_empty_qty_string_skips(self):
        """Empty string qty is treated as missing."""
        data = {
            "orders": [
                {"order_id": "x", "price": "50000", "qty": "", "ts_event_ns": str(TS)},
            ]
        }
        result = _parse_open_orders(data)
        assert len(result) == 0

    def test_zero_qty_is_valid(self):
        """Explicit zero qty (not missing) is valid - true_zero vs missing."""
        data = {
            "orders": [
                {"order_id": "zero-qty", "price": "50000", "qty": "0", "ts_event_ns": str(TS)},
            ]
        }
        result = _parse_open_orders(data)
        assert len(result) == 1
        assert result[0].qty == 0.0

    def test_filled_qty_defaults_to_zero_when_missing(self):
        """Missing filled_qty defaults to 0.0 (not aliased to qty)."""
        data = {
            "orders": [
                {"order_id": "o", "price": "50000", "qty": "1.5", "ts_event_ns": str(TS)},
            ]
        }
        result = _parse_open_orders(data)
        assert len(result) == 1
        assert result[0].filled_qty == 0.0
        assert result[0].qty == 1.5

    def test_empty_orders_list(self):
        """Empty orders list returns empty."""
        data = {"orders": []}
        result = _parse_open_orders(data)
        assert result == []
