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


def test_execution_lane_worker_run_once_route_claims_queued_paper_command_and_returns_report() -> None:
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
    command_response = app.post(
        "/api/execution-lane/commands",
        json={
            "tenant_id": "tenant_a",
            "project_id": "project_alpha",
            "runtime_profile_id": "rp_paper_tradingnode",
            "lane_mode": "paper",
            "adapter_id": "BINANCE_PERP",
            "venue": "BINANCE",
            "venue_account_id": "SIM-BINANCE-001",
            "trade_action_id": "ta_paper_001",
            "source_event_id": "gate_evt_paper_001",
            "idempotency_key": "gate_evt_paper_001:ta_paper_001",
            "strategy_lineage_id": "lineage_ema_rsi",
            "strategy_version_id": "strategy_001_v004",
            "order_intent": {"side": "BUY", "instrument_id": "BTCUSDT-PERP.BINANCE", "quantity": "0.01"},
            "risk_decision": {"status": "approved", "risk_profile_id": "risk_paper_default"},
        },
    )

    response = app.post(
        "/api/execution-lane/worker/run-once",
        json={"runtime_profile_id": "rp_paper_tradingnode", "worker_id": "web_exec_worker"},
    )
    status_response = app.get("/api/execution-lane/status?runtime_profile_id=rp_paper_tradingnode")

    payload = response.json()
    assert command_response.status_code == 201
    assert response.status_code == 202
    assert payload["command_id"] == command_response.json()["command_id"]
    assert payload["report_type"] == "tradingnode_runtime_plan"
    assert payload["payload"]["node_runtime"] == "python_trading_node"
    assert payload["payload"]["may_submit_order"] is False
    assert status_response.json()["reported_commands"] == 1


def test_execution_lane_worker_run_once_route_fails_closed_without_queued_command() -> None:
    app = create_app()

    response = app.post(
        "/api/execution-lane/worker/run-once",
        json={"runtime_profile_id": "missing", "worker_id": "web_exec_worker"},
    )

    assert response.status_code == 409
    assert response.json()["error"] == "execution_lane_command_not_available"
