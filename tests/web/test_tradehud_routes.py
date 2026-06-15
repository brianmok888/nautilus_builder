"""Tests for TradeHUD API routes — verify no submit_order exposure."""

import pytest
from services.api.routes.tradehud import (
    tradehud_snapshot_payload,
    tradehud_health_payload,
    tradehud_replay_payload,
)


class TestTradehudSnapshotEndpoint:
    def test_returns_valid_snapshot(self):
        data = tradehud_snapshot_payload("BTCUSDT-PERP")
        assert data["provenance"] == "mock"
        assert data["book_top"]["symbol"] == "BTCUSDT-PERP"

    def test_no_credentials_in_response(self):
        data = tradehud_snapshot_payload()
        data_str = str(data).lower()
        for forbidden in ["api_key", "secret_key", "private_key", "binance_secret"]:
            assert forbidden not in data_str

    def test_synthetic_provenance(self):
        data = tradehud_snapshot_payload()
        assert data["book_l2"]["provenance"] == "mock"
        assert data["book_l2"]["source_status"] == "synthetic"


class TestTradehudHealthEndpoint:
    def test_returns_health(self):
        data = tradehud_health_payload()
        assert data["status"] == "ok"
        assert data["mode"] == "mock"


class TestTradehudReplayEndpoint:
    def test_returns_events(self):
        data = tradehud_replay_payload("BTCUSDT-PERP")
        assert "events" in data
        assert len(data["events"]) > 0
        assert data["provenance"] == "mock"


class TestNoSubmitOrder:
    def test_no_submit_order_in_routes(self):
        """Ensure route module never exposes submit_order."""
        import inspect
        from services.api.routes import tradehud as mod
        source = inspect.getsource(mod)
        assert "submit_order" not in source
        assert "create_trade_action" not in source.lower()
