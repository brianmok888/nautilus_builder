from __future__ import annotations

import pytest

from packages.execution_lane import ExecutionLaneService
from packages.execution_lane.nautilus_runtime import build_trading_node_runtime_plan
from services.workers.execution_lane_worker import run_execution_lane_worker_once


def _paper_profile() -> dict[str, object]:
    return {
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
        "ui_enabled": True,
        "paper_controls_enabled": True,
        "consumes_stream": "builder.execution.commands.paper.project_alpha.binance",
    }


def _paper_command() -> dict[str, object]:
    return {
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
    }


def _live_profile() -> dict[str, object]:
    return {
        "tenant_id": "tenant_a",
        "project_id": "project_alpha",
        "runtime_profile_id": "rp_live_tradingnode",
        "profile_name": "Live TradingNode lane",
        "lane_mode": "live",
        "enabled": True,
        "adapter_id": "BINANCE_PERP",
        "venue": "BINANCE",
        "venue_account_id": "MAIN-BINANCE-001",
        "ui_enabled": True,
        "live_controls_enabled": True,
        "advisory_only": False,
        "manual_review_required": True,
        "live_trading_enabled": True,
        "execution_authority": True,
        "may_submit_order": True,
        "risk_profile_id": "risk_live_001",
        "credential_slot_ref": "credslot://server/binance_main",
        "activated_by": "ops_user",
        "activated_at": "2026-05-26T12:00:00Z",
        "config_checksum": "a" * 64,
        "manual_review_id": "manual_review_001",
        "data_tester_evidence_ref": "artifact://builder/project_alpha/ops_user/data_tester/binance.json",
        "exec_tester_evidence_ref": "artifact://builder/project_alpha/ops_user/exec_tester/binance.json",
        "reconciliation_evidence_ref": "artifact://builder/project_alpha/ops_user/reconciliation/binance.json",
        "consumes_stream": "builder.execution.commands.live.project_alpha.binance",
    }


def _live_command() -> dict[str, object]:
    return {
        **_paper_command(),
        "runtime_profile_id": "rp_live_tradingnode",
        "lane_mode": "live",
        "idempotency_key": "live:ta_live_001",
        "trade_action_id": "ta_live_001",
        "source_event_id": "gate_evt_live_001",
        "adapter_id": "BINANCE_PERP",
        "venue": "BINANCE",
        "venue_account_id": "MAIN-BINANCE-001",
        "live_trading_enabled": True,
        "execution_authority": True,
        "may_submit_order": True,
        "promotion_approval_id": "approval_001",
        "risk_profile_id": "risk_live_001",
        "credential_slot_ref": "credslot://server/binance_main",
        "manual_review_id": "manual_review_001",
        "data_tester_evidence_ref": "artifact://builder/project_alpha/ops_user/data_tester/binance.json",
        "exec_tester_evidence_ref": "artifact://builder/project_alpha/ops_user/exec_tester/binance.json",
        "reconciliation_evidence_ref": "artifact://builder/project_alpha/ops_user/reconciliation/binance.json",
        "risk_decision": {"status": "approved", "risk_profile_id": "risk_live_001"},
    }


def test_paper_profile_builds_python_tradingnode_plan_without_live_authority() -> None:
    service = ExecutionLaneService()
    profile = service.register_profile(_paper_profile())

    plan = build_trading_node_runtime_plan(profile)

    assert plan.readiness_status == "READY"
    assert plan.node_runtime == "python_trading_node"
    assert plan.runtime_label == "python_live_integration_specific"
    assert plan.future_runtime == "rust_live_node"
    assert plan.runtime_environment == "sandbox"
    assert plan.live_trading_enabled is False
    assert plan.execution_authority is False
    assert plan.may_submit_order is False
    assert plan.strategy_lane_coupled is False
    assert plan.browser_credentials_allowed is False
    assert plan.credential_inputs_allowed is False
    assert plan.credential_slot_ref is None
    assert plan.nautilus_imports == [
        "nautilus_trader.config.TradingNodeConfig",
        "nautilus_trader.config.LiveExecEngineConfig",
        "nautilus_trader.live.node.TradingNode",
    ]
    assert plan.config_contract["exec_engine"]["reconciliation"] is True
    assert plan.config_contract["exec_engine"]["reconciliation_lookback_mins"] >= 60
    assert plan.config_contract["exec_engine"]["reconciliation_startup_delay_secs"] >= 10


def test_live_profile_requires_evidence_gates_before_submit_authority() -> None:
    profile_payload = _live_profile()
    profile_payload.pop("exec_tester_evidence_ref")

    service = ExecutionLaneService()
    with pytest.raises(ValueError, match="exec_tester_evidence_ref"):
        service.register_profile(profile_payload)

    disabled_profile_payload = _live_profile()
    disabled_profile_payload.update(
        {
            "runtime_profile_id": "rp_live_disabled",
            "enabled": False,
            "live_controls_enabled": False,
            "live_trading_enabled": False,
            "execution_authority": False,
            "may_submit_order": False,
        }
    )
    profile = service.register_profile(disabled_profile_payload)
    plan = build_trading_node_runtime_plan(profile)

    assert plan.readiness_status == "BLOCKED"
    assert plan.may_submit_order is False
    assert "live_trading_enabled" in plan.blocked_reasons
    assert "execution_authority" in plan.blocked_reasons
    assert "may_submit_order" in plan.blocked_reasons


def test_live_profile_with_full_gates_builds_authority_plan_without_browser_credentials() -> None:
    service = ExecutionLaneService()
    profile = service.register_profile(_live_profile())
    command = service.enqueue_command(_live_command())

    plan = build_trading_node_runtime_plan(profile, command=command)

    assert plan.readiness_status == "READY"
    assert plan.node_runtime == "python_trading_node"
    assert plan.runtime_environment == "live"
    assert plan.live_trading_enabled is True
    assert plan.execution_authority is True
    assert plan.may_submit_order is True
    assert plan.browser_credentials_allowed is False
    assert plan.credential_inputs_allowed is False
    assert plan.credential_slot_ref == "credslot://server/binance_main"
    assert plan.strategy_lineage_id == "lineage_ema_rsi"
    assert plan.strategy_version_id == "strategy_001_v004"
    assert plan.promotion_approval_id == "approval_001"
    assert plan.evidence_refs["data_tester"] == "artifact://builder/project_alpha/ops_user/data_tester/binance.json"
    assert plan.evidence_refs["exec_tester"] == "artifact://builder/project_alpha/ops_user/exec_tester/binance.json"
    assert plan.evidence_refs["reconciliation"] == "artifact://builder/project_alpha/ops_user/reconciliation/binance.json"
    assert "api_key" not in str(plan.model_dump(mode="json")).lower()


def test_live_command_evidence_refs_must_match_profile_scope() -> None:
    service = ExecutionLaneService()
    service.register_profile(_live_profile())
    command = _live_command()
    command["exec_tester_evidence_ref"] = "artifact://builder/project_alpha/ops_user/exec_tester/other-venue.json"

    with pytest.raises(ValueError, match="exec_tester_evidence_ref"):
        service.enqueue_command(command)


def test_runtime_contract_rejects_client_side_secret_fields() -> None:
    service = ExecutionLaneService()
    profile = _paper_profile()
    profile["api_key"] = "browser-secret"
    with pytest.raises(ValueError, match="credentials|Extra inputs"):
        service.register_profile(profile)

    service.register_profile(_paper_profile())
    command = _paper_command()
    command["risk_decision"] = {"status": "approved", "private_key": "should-not-be-here"}
    with pytest.raises(ValueError, match="credentials"):
        service.enqueue_command(command)


def test_worker_claims_command_and_records_tradingnode_runtime_report() -> None:
    service = ExecutionLaneService()
    service.register_profile(_paper_profile())
    command = service.enqueue_command(_paper_command())

    report = run_execution_lane_worker_once(service=service, runtime_profile_id="rp_paper_tradingnode", worker_id="exec_worker_1")

    assert report.command_id == command.command_id
    assert report.report_type == "tradingnode_runtime_plan"
    assert report.payload["node_runtime"] == "python_trading_node"
    assert report.payload["runtime_label"] == "python_live_integration_specific"
    assert report.payload["may_submit_order"] is False
    assert report.payload["strategy_lane_coupled"] is False
    assert service.snapshot(runtime_profile_id="rp_paper_tradingnode")["reported_commands"] == 1

def test_worker_report_includes_credential_slot_and_risk_gate_without_secrets(tmp_path) -> None:
    service = ExecutionLaneService(credential_env_dir=tmp_path)
    slot = service.create_credential_slot(
        {
            "tenant_id": "tenant_a",
            "project_id": "project_alpha",
            "runtime_profile_id": "rp_paper_tradingnode",
            "adapter_id": "BINANCE_PERP",
            "venue": "BINANCE",
            "lane_mode": "paper",
            "requested_by": "ops_user",
            "credential_values": {"BINANCE_API_KEY": "test-binance-key"},
        }
    )
    profile = _paper_profile()
    profile["credential_slot_ref"] = slot.credential_slot_ref
    service.register_profile(profile)
    service.enqueue_command(_paper_command())

    report = run_execution_lane_worker_once(service=service, runtime_profile_id="rp_paper_tradingnode", worker_id="exec_worker_1")

    assert report.payload["risk_gate_status"] == "PASS"
    assert report.payload["credential_slot_bound"] is True
    assert report.payload["credential_slot_ref"] == slot.credential_slot_ref
    assert "test-binance-key" not in str(report.model_dump(mode="json"))


def test_paper_session_start_resolves_credential_slot_builds_config_and_emits_lifecycle(tmp_path) -> None:
    from packages.execution_lane.sessions import ContractTradingNodeSessionRunner
    from services.workers.execution_lane_worker import start_execution_lane_paper_session

    service = ExecutionLaneService(credential_env_dir=tmp_path)
    slot = service.create_credential_slot(
        {
            "tenant_id": "tenant_a",
            "project_id": "project_alpha",
            "runtime_profile_id": "rp_paper_tradingnode",
            "adapter_id": "BINANCE_PERP",
            "venue": "BINANCE",
            "lane_mode": "paper",
            "requested_by": "ops_user",
            "credential_values": {
                "BINANCE_API_KEY": "test-binance-key",
                "BINANCE_API_SECRET": "test-binance-secret",
                "BINANCE_TESTNET": "true",
            },
        }
    )
    profile = _paper_profile()
    profile["credential_slot_ref"] = slot.credential_slot_ref
    service.register_profile(profile)
    command = service.enqueue_command(_paper_command())

    session = start_execution_lane_paper_session(
        service=service,
        runtime_profile_id="rp_paper_tradingnode",
        command_id=command.command_id,
        worker_id="web_exec_worker",
        runner=ContractTradingNodeSessionRunner(),
    )

    assert session.status == "RUNNING"
    assert session.lifecycle_status == "RUNNING"
    assert session.command_id == command.command_id
    assert session.credential_slot_ref == slot.credential_slot_ref
    assert session.credential_env_keys == ["BINANCE_API_KEY", "BINANCE_API_SECRET", "BINANCE_TESTNET"]
    assert session.tradingnode_config["config_type"] == "TradingNodeConfig"
    assert session.tradingnode_config["environment"] == "sandbox"
    assert session.tradingnode_config["data_clients"]["BINANCE"] == "BinanceDataClientConfig"
    assert session.tradingnode_config["exec_clients"]["BINANCE"] == "BinanceExecClientConfig"
    assert session.attached_strategy["strategy_version_id"] == "strategy_001_v004"
    assert session.attached_strategy["may_submit_order"] is False
    assert [event["status"] for event in session.lifecycle_events] == ["INITIALIZED", "CONFIG_BUILT", "BUILD", "RUNNING"]
    assert session.browser_credentials_allowed is False
    assert session.may_submit_order is False
    assert "test-binance-key" not in str(session.model_dump(mode="json"))
    assert service.snapshot(runtime_profile_id="rp_paper_tradingnode")["running_sessions"] == 1


def test_paper_session_stop_disposes_runner_and_records_lifecycle(tmp_path) -> None:
    from packages.execution_lane.sessions import ContractTradingNodeSessionRunner
    from services.workers.execution_lane_worker import start_execution_lane_paper_session, stop_execution_lane_session

    service = ExecutionLaneService(credential_env_dir=tmp_path)
    slot = service.create_credential_slot(
        {
            "tenant_id": "tenant_a",
            "project_id": "project_alpha",
            "runtime_profile_id": "rp_paper_tradingnode",
            "adapter_id": "BINANCE_PERP",
            "venue": "BINANCE",
            "lane_mode": "paper",
            "requested_by": "ops_user",
            "credential_values": {"BINANCE_API_KEY": "test-binance-key", "BINANCE_API_SECRET": "test-binance-secret"},
        }
    )
    profile = _paper_profile()
    profile["credential_slot_ref"] = slot.credential_slot_ref
    service.register_profile(profile)
    command = service.enqueue_command(_paper_command())
    session = start_execution_lane_paper_session(
        service=service,
        runtime_profile_id="rp_paper_tradingnode",
        command_id=command.command_id,
        worker_id="web_exec_worker",
        runner=ContractTradingNodeSessionRunner(),
    )

    stopped = stop_execution_lane_session(service=service, session_id=session.session_id, worker_id="web_exec_worker")

    assert stopped.status == "DISPOSED"
    assert stopped.lifecycle_status == "DISPOSED"
    assert [event["status"] for event in stopped.lifecycle_events][-2:] == ["STOPPED", "DISPOSED"]
    assert service.snapshot(runtime_profile_id="rp_paper_tradingnode")["running_sessions"] == 0


def test_paper_session_start_requires_server_side_credential_slot(tmp_path) -> None:
    from packages.execution_lane.sessions import ContractTradingNodeSessionRunner
    from services.workers.execution_lane_worker import start_execution_lane_paper_session

    service = ExecutionLaneService(credential_env_dir=tmp_path)
    service.register_profile(_paper_profile())
    command = service.enqueue_command(_paper_command())

    with pytest.raises(ValueError, match="credential_slot_ref"):
        start_execution_lane_paper_session(
            service=service,
            runtime_profile_id="rp_paper_tradingnode",
            command_id=command.command_id,
            worker_id="web_exec_worker",
            runner=ContractTradingNodeSessionRunner(),
        )
