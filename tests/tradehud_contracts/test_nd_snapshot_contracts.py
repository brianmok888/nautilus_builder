"""
ND snapshot contract tests.

Tests the mixed runtime sequence fixture to ensure all event types
produce a coherent snapshot.
"""
import json
from pathlib import Path

import pytest
from packages.tradehud_contracts.redis_adapter import (
    _parse_book_top,
    _parse_trade,
    _parse_signal,
    _parse_gate,
    _parse_execution,
    build_snapshot_from_redis,
)
from packages.tradehud_contracts.models import TradeHudSnapshot

FIXTURE_DIR = Path(__file__).parent.parent / "fixtures" / "tradehud_nd_contracts"
TS = 1700000000_000000000


def load_fixture(fname):
    path = FIXTURE_DIR / fname
    return [json.loads(line) for line in path.read_text().strip().split("\n") if line.strip()]


class TestMixedRuntimeSequence:
    """Mixed sequence fixture should produce coherent snapshot."""

    def test_mixed_sequence_loads(self):
        records = load_fixture("nd_mixed_runtime_sequence.jsonl")
        assert len(records) >= 4

    def test_book_top_from_mixed(self):
        records = load_fixture("nd_mixed_runtime_sequence.jsonl")
        book_top_data = next(r for r in records if r["event_type"] == "book_top")
        result = _parse_book_top(book_top_data)
        assert result is not None
        assert result.symbol == "BTCUSDT-PERP"

    def test_trade_from_mixed(self):
        records = load_fixture("nd_mixed_runtime_sequence.jsonl")
        trade_data = next(r for r in records if r["event_type"] == "trade")
        result = _parse_trade(trade_data)
        assert result is not None
        assert result.price == 50000.5

    def test_signal_from_mixed(self):
        records = load_fixture("nd_mixed_runtime_sequence.jsonl")
        signal_data = next(r for r in records if r["event_type"] == "signal")
        result = _parse_signal(signal_data)
        assert result is not None
        assert result.direction == "long"

    def test_gate_from_mixed(self):
        records = load_fixture("nd_mixed_runtime_sequence.jsonl")
        gate_data = next(r for r in records if r["event_type"] == "gate")
        result = _parse_gate(gate_data)
        assert result is not None
        assert result.decision == "APPROVED"

    def test_execution_from_mixed(self):
        records = load_fixture("nd_mixed_runtime_sequence.jsonl")
        exec_data = next(r for r in records if r["event_type"] == "execution")
        result = _parse_execution(exec_data)
        assert result is not None
        assert result.status == "FILLED"


class TestBadMissingFields:
    """Bad fixtures must be rejected by parsers."""

    def test_missing_ask_price_rejected(self):
        records = load_fixture("nd_bad_missing_fields.jsonl")
        bad_book = next(r for r in records if r.get("event_type") == "book_top")
        result = _parse_book_top(bad_book)
        assert result is None, "Missing ask_price must be rejected"

    def test_missing_qty_rejected(self):
        records = load_fixture("nd_bad_missing_fields.jsonl")
        bad_trade = next(r for r in records if r.get("event_type") == "trade" and "qty" not in r)
        result = _parse_trade(bad_trade)
        assert result is None, "Missing qty must be rejected"

    def test_missing_ts_rejected(self):
        records = load_fixture("nd_bad_missing_fields.jsonl")
        bad_trade = next(r for r in records if r.get("event_type") == "trade" and "ts_event_ns" not in r)
        result = _parse_trade(bad_trade)
        assert result is None, "Missing ts must be rejected"


class TestSnapshotContract:
    def test_empty_snapshot_has_no_order_authority(self):
        snap = TradeHudSnapshot()
        assert snap.book_top is None
        assert snap.latest_trade_action is None
        assert snap.latest_execution_report is None

    def test_snapshot_from_entries_is_read_only(self):
        entries = {
            "book_top": {
                b"symbol": b"BTCUSDT-PERP", b"bid_price": b"50000",
                b"ask_price": b"50001", b"ts_event_ns": str(TS).encode(),
            },
        }
        snap = build_snapshot_from_redis(entries)
        assert snap.book_top is not None
        assert snap.provenance in ("mock", "redis", "redis_seeded", "unknown")
