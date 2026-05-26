from __future__ import annotations

from services.api.app import create_app


def test_execution_lane_status_reports_venue_binding_and_ui_feature_flags() -> None:
    app = create_app()
    app.post(
        "/api/execution-lane/profiles",
        json={
            "tenant_id": "tenant_a",
            "project_id": "project_alpha",
            "runtime_profile_id": "rp_paper_binance",
            "profile_name": "Binance paper lane",
            "lane_mode": "paper",
            "enabled": True,
            "paper_trading_enabled": True,
            "adapter_id": "BINANCE_PERP",
            "venue": "BINANCE",
            "venue_account_id": "SIM-BINANCE-001",
            "ui_enabled": True,
            "paper_controls_enabled": True,
            "consumes_stream": "builder.execution.commands.paper.project_alpha.binance",
        },
    )

    response = app.get("/api/execution-lane/status?runtime_profile_id=rp_paper_binance")

    payload = response.json()
    assert response.status_code == 200
    assert payload["venue_bindings"][0]["adapter_id"] == "BINANCE_PERP"
    assert payload["venue_bindings"][0]["venue"] == "BINANCE"
    assert payload["ui_features"]["execution_lane_ui_enabled"] is True
    assert payload["ui_features"]["paper_controls_enabled"] is True
    assert payload["ui_features"]["live_controls_enabled"] is False
    assert payload["ui_features"]["credential_inputs_allowed"] is False


def test_execution_lane_command_route_rejects_mismatched_venue() -> None:
    app = create_app()
    app.post(
        "/api/execution-lane/profiles",
        json={
            "tenant_id": "tenant_a",
            "project_id": "project_alpha",
            "runtime_profile_id": "rp_paper_binance",
            "profile_name": "Binance paper lane",
            "lane_mode": "paper",
            "enabled": True,
            "paper_trading_enabled": True,
            "adapter_id": "BINANCE_PERP",
            "venue": "BINANCE",
            "consumes_stream": "builder.execution.commands.paper.project_alpha.binance",
        },
    )

    response = app.post(
        "/api/execution-lane/commands",
        json={
            "tenant_id": "tenant_a",
            "project_id": "project_alpha",
            "runtime_profile_id": "rp_paper_binance",
            "lane_mode": "paper",
            "adapter_id": "BINANCE_PERP",
            "venue": "OKX",
            "trade_action_id": "ta_wrong_venue",
            "source_event_id": "gate_evt_wrong_venue",
            "idempotency_key": "wrong-venue",
            "strategy_lineage_id": "lineage_ema_rsi",
            "strategy_version_id": "strategy_001_v004",
            "order_intent": {"side": "BUY", "instrument_id": "BTCUSDT-PERP.BINANCE", "quantity": "0.01"},
            "risk_decision": {"status": "approved", "risk_profile_id": "risk_paper_default"},
        },
    )

    assert response.status_code == 422
    assert response.json()["error"] == "invalid_execution_lane_command"
    assert "venue does not match" in response.json()["details"]
