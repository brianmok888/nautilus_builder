"""Tests for tradehud_contracts — observational snapshot schema validation.

No submit_order. No credentials. No TradeAction creation by UI.
"""

import pytest
from packages.tradehud_contracts.mock_data import generate_snapshot
from packages.tradehud_contracts.service import TradeHudService


class TestSnapshotSchema:
    def test_snapshot_generates_all_fields(self):
        snap = generate_snapshot("BTCUSDT-PERP", seed=42)
        assert snap.book_top is not None
        assert snap.book_l2 is not None
        assert snap.latest_signal_preview is not None
        assert snap.latest_gate_decision is not None
        assert snap.latest_trade_action is not None
        assert snap.latest_execution_report is not None
        assert snap.account is not None
        assert len(snap.positions) > 0
        assert len(snap.assets) > 0
        assert snap.quant_levels is not None
        assert snap.tick_to_trade is not None
        assert snap.runtime_health is not None

    def test_snapshot_is_deterministic(self):
        snap1 = generate_snapshot("BTCUSDT-PERP", seed=42)
        snap2 = generate_snapshot("BTCUSDT-PERP", seed=42)
        assert snap1.book_top.bid_price == snap2.book_top.bid_price
        assert snap1.latest_signal_preview.confidence_score == snap2.latest_signal_preview.confidence_score

    def test_snapshot_provenance_is_mock(self):
        snap = generate_snapshot("BTCUSDT-PERP", seed=42)
        assert snap.provenance == "mock"
        assert snap.book_l2.source_status == "synthetic"
        assert snap.book_l2.provenance == "mock"

    def test_eth_symbol_supported(self):
        snap = generate_snapshot("ETHUSDT-PERP", seed=42)
        assert snap.book_top.symbol == "ETHUSDT-PERP"

    def test_snapshot_serializes_to_json(self):
        snap = generate_snapshot("BTCUSDT-PERP", seed=42)
        data = snap.model_dump(mode="json")
        assert isinstance(data, dict)
        assert data["provenance"] == "mock"
        assert data["book_top"]["symbol"] == "BTCUSDT-PERP"


class TestNoCredentialsExposed:
    def test_snapshot_has_no_api_keys(self):
        snap = generate_snapshot("BTCUSDT-PERP", seed=42)
        data = snap.model_dump(mode="json")
        data_str = str(data).lower()
        for forbidden in [
            "api_key", "secret_key", "private_key",
            "binance_secret", "api_secret", "password",
            "token", "credential",
        ]:
            assert forbidden not in data_str, f"Found forbidden term '{forbidden}' in snapshot"


class TestTradeActionEvidenceOnly:
    def test_trade_action_created_by_runtime(self):
        snap = generate_snapshot("BTCUSDT-PERP", seed=42)
        ta = snap.latest_trade_action
        assert ta is not None
        assert ta.created_by == "run_gate_engine"
        # Must have hash linking to gate decision
        assert ta.source_gate_decision_hash is not None
        assert ta.trade_action_hash is not None

    def test_execution_report_has_exchange_evidence(self):
        snap = generate_snapshot("BTCUSDT-PERP", seed=42)
        rep = snap.latest_execution_report
        assert rep is not None
        assert rep.status == "FILLED"
        assert rep.exchange_order_id is not None
        assert rep.client_order_id is not None

    def test_signal_preview_is_not_executable(self):
        snap = generate_snapshot("BTCUSDT-PERP", seed=42)
        sig = snap.latest_signal_preview
        assert sig is not None
        assert "NOT EXECUTABLE" in sig.preview_note


class TestService:
    def test_service_returns_snapshot(self):
        svc = TradeHudService()
        snap = svc.get_snapshot()
        assert snap.book_top is not None

    def test_service_health(self):
        svc = TradeHudService()
        health = svc.get_health()
        assert health["status"] == "ok"
        assert health["mode"] == "mock"
        assert health["has_runtime"] is False
        assert health["has_redis"] is False
