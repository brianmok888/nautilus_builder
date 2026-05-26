from __future__ import annotations

from services.api.app import create_app


def test_execution_lane_status_route_is_independent_from_strategy_lane() -> None:
    app = create_app()

    response = app.get("/api/execution-lane/status")

    payload = response.json()
    assert response.status_code == 200
    assert payload["mode"] == "execution_lane"
    assert payload["strategy_lane_coupled"] is False
    assert payload["may_submit_order"] is False


def test_execution_lane_profile_and_command_routes_use_package_policy() -> None:
    app = create_app()

    profile_response = app.post(
        "/api/execution-lane/profiles",
        json={
            "tenant_id": "tenant_a",
            "project_id": "project_alpha",
            "runtime_profile_id": "rp_paper_001",
            "profile_name": "Paper lane",
            "lane_mode": "paper",
            "enabled": True,
            "paper_trading_enabled": True,
            "consumes_stream": "builder.execution.commands.paper.project_alpha",
        },
    )
    command_response = app.post(
        "/api/execution-lane/commands",
        json={
            "tenant_id": "tenant_a",
            "project_id": "project_alpha",
            "runtime_profile_id": "rp_paper_001",
            "lane_mode": "paper",
            "trade_action_id": "ta_001",
            "source_event_id": "gate_evt_001",
            "idempotency_key": "gate_evt_001:ta_001",
            "strategy_lineage_id": "lineage_ema_rsi",
            "strategy_version_id": "strategy_001_v004",
            "order_intent": {"side": "BUY", "instrument_id": "BTCUSDT-PERP.BINANCE", "quantity": "0.01"},
            "risk_decision": {"status": "approved", "risk_profile_id": "risk_paper_default"},
        },
    )

    assert profile_response.status_code == 201
    assert profile_response.json()["strategy_lane_coupled"] is False
    assert command_response.status_code == 201
    assert command_response.json()["may_submit_order"] is False
    assert command_response.json()["status"] == "QUEUED"


def test_execution_lane_route_rejects_live_command_without_gates() -> None:
    app = create_app()
    app.post(
        "/api/execution-lane/profiles",
        json={
            "tenant_id": "tenant_a",
            "project_id": "project_alpha",
            "runtime_profile_id": "rp_live_disabled",
            "profile_name": "Disabled live lane",
            "lane_mode": "live",
            "enabled": False,
            "consumes_stream": "builder.execution.commands.live.project_alpha",
        },
    )

    response = app.post(
        "/api/execution-lane/commands",
        json={
            "tenant_id": "tenant_a",
            "project_id": "project_alpha",
            "runtime_profile_id": "rp_live_disabled",
            "lane_mode": "live",
            "trade_action_id": "ta_live_001",
            "source_event_id": "gate_evt_live_001",
            "idempotency_key": "live:ta_live_001",
            "strategy_lineage_id": "lineage_ema_rsi",
            "strategy_version_id": "strategy_001_v004",
            "order_intent": {"side": "BUY", "instrument_id": "BTCUSDT-PERP.BINANCE", "quantity": "0.01"},
            "risk_decision": {"status": "approved", "risk_profile_id": "risk_live_001"},
            "live_trading_enabled": True,
            "execution_authority": True,
            "may_submit_order": True,
            "promotion_approval_id": "approval_001",
            "risk_profile_id": "risk_live_001",
            "credential_slot_ref": "credslot://server/binance_main",
        },
    )

    assert response.status_code == 422
    assert response.json()["error"] == "invalid_execution_lane_command"
    assert "profile is not live-enabled" in response.json()["details"]
