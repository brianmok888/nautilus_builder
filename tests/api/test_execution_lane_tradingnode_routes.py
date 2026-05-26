from __future__ import annotations

from services.api.app import create_app


def test_execution_lane_runtime_plan_route_returns_paper_tradingnode_contract() -> None:
    app = create_app()
    app.post(
        "/api/execution-lane/profiles",
        json={
            "tenant_id": "tenant_a",
            "project_id": "project_alpha",
            "runtime_profile_id": "rp_paper_tradingnode",
            "profile_name": "Paper TradingNode lane",
            "lane_mode": "paper",
            "enabled": True,
            "paper_trading_enabled": True,
            "adapter_id": "BINANCE_PERP",
            "venue": "BINANCE",
            "venue_account_id": "SIM-BINANCE-001",
            "consumes_stream": "builder.execution.commands.paper.project_alpha.binance",
        },
    )

    response = app.get("/api/execution-lane/runtime-plan?runtime_profile_id=rp_paper_tradingnode")

    payload = response.json()
    assert response.status_code == 200
    assert payload["node_runtime"] == "python_trading_node"
    assert payload["runtime_label"] == "python_live_integration_specific"
    assert payload["runtime_environment"] == "sandbox"
    assert payload["may_submit_order"] is False
    assert payload["browser_credentials_allowed"] is False
    assert payload["config_contract"]["exec_engine"]["reconciliation"] is True


def test_execution_lane_runtime_plan_route_fails_closed_for_unknown_profile() -> None:
    app = create_app()

    response = app.get("/api/execution-lane/runtime-plan?runtime_profile_id=missing")

    assert response.status_code == 404
    assert response.json()["error"] == "execution_lane_profile_not_found"
