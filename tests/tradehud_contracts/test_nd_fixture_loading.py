"""
ND fixture loading contract tests.

Verifies all fixture files exist, are valid JSONL, and contain deterministic values.
"""
import json
from pathlib import Path

import pytest

FIXTURE_DIR = Path(__file__).parent.parent / "fixtures" / "tradehud_nd_contracts"

EXPECTED_FIXTURES = [
    "nd_market_book_top.jsonl",
    "nd_market_book_l2.jsonl",
    "nd_market_trades.jsonl",
    "nd_strategy_signal_preview.jsonl",
    "nd_gate_decision.jsonl",
    "nd_trade_action.jsonl",
    "nd_execution_report.jsonl",
    "nd_health.jsonl",
    "nd_quant_levels_context.jsonl",
    "nd_tick_to_trade_trace.jsonl",
    "nd_account_snapshot.jsonl",
    "nd_position_snapshot.jsonl",
    "nd_order_snapshot.jsonl",
    "nd_order_event.jsonl",
    "nd_mixed_runtime_sequence.jsonl",
    "nd_bad_missing_fields.jsonl",
    "nd_stale_missing_true_zero_cases.jsonl",
]

MIN_RECORDS = {
    "nd_market_book_top.jsonl": 2,
    "nd_market_trades.jsonl": 2,
    "nd_gate_decision.jsonl": 3,
    "nd_mixed_runtime_sequence.jsonl": 4,
    "nd_bad_missing_fields.jsonl": 3,
    "nd_stale_missing_true_zero_cases.jsonl": 3,
}


def load_fixture(fname: str) -> list[dict]:
    path = FIXTURE_DIR / fname
    records = []
    for line in path.read_text().strip().split("\n"):
        if line.strip():
            records.append(json.loads(line))
    return records


class TestFixtureFiles:
    @pytest.mark.parametrize("fname", EXPECTED_FIXTURES)
    def test_fixture_file_exists(self, fname):
        assert (FIXTURE_DIR / fname).exists(), f"Missing fixture: {fname}"

    @pytest.mark.parametrize("fname", EXPECTED_FIXTURES)
    def test_fixture_is_valid_jsonl(self, fname):
        records = load_fixture(fname)
        assert len(records) >= 1, f"{fname} has no records"
        for r in records:
            assert isinstance(r, dict), f"{fname} has non-dict line"

    def test_total_fixture_count(self):
        actual = [f.name for f in FIXTURE_DIR.glob("*.jsonl")]
        assert len(actual) == len(EXPECTED_FIXTURES), \
            f"Expected {len(EXPECTED_FIXTURES)} fixtures, got {len(actual)}"

    def test_min_record_counts(self):
        for fname, min_n in MIN_RECORDS.items():
            records = load_fixture(fname)
            assert len(records) >= min_n, \
                f"{fname} expected >= {min_n} records, got {len(records)}"


class TestFixtureDeterminism:
    def test_book_top_has_deterministic_prices(self):
        records = load_fixture("nd_market_book_top.jsonl")
        prices = {r["bid_price"] for r in records}
        assert 50000.0 in prices
        assert 3000.0 in prices

    def test_trades_have_deterministic_ts(self):
        records = load_fixture("nd_market_trades.jsonl")
        for r in records:
            ts = r["ts_event_ns"]
            assert ts >= 1700000000_000000000, "ts should be deterministic base"
            assert ts < 1800000000_000000000, "ts should not be now()"

    def test_gate_decisions_have_all_three_types(self):
        records = load_fixture("nd_gate_decision.jsonl")
        decisions = {r["decision"] for r in records}
        assert "APPROVED" in decisions
        assert "REJECTED" in decisions
        assert "HOLD" in decisions

    def test_symbols_are_btc_and_eth_only(self):
        for fname in ["nd_market_book_top.jsonl", "nd_market_trades.jsonl"]:
            records = load_fixture(fname)
            symbols = {r.get("symbol", "") for r in records}
            assert symbols.issubset({"BTCUSDT-PERP", "ETHUSDT-PERP"}), \
                f"Unexpected symbols in {fname}: {symbols}"
