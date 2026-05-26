from __future__ import annotations

import pytest

from packages.execution_lane import ExecutionCommandStatus, ExecutionLaneMode, ExecutionLaneService


def _paper_profile() -> dict[str, object]:
    return {
        "tenant_id": "tenant_a",
        "project_id": "project_alpha",
        "runtime_profile_id": "rp_paper_001",
        "profile_name": "Paper execution lane",
        "lane_mode": "paper",
        "enabled": True,
        "paper_trading_enabled": True,
        "adapter_id": "BINANCE_PERP",
        "venue": "BINANCE",
        "venue_account_id": "SIM-BINANCE-001",
        "consumes_stream": "builder.execution.commands.paper.project_alpha",
    }


def _paper_command() -> dict[str, object]:
    return {
        "tenant_id": "tenant_a",
        "project_id": "project_alpha",
        "runtime_profile_id": "rp_paper_001",
        "lane_mode": "paper",
        "adapter_id": "BINANCE_PERP",
        "venue": "BINANCE",
        "venue_account_id": "SIM-BINANCE-001",
        "trade_action_id": "ta_001",
        "source_event_id": "gate_evt_001",
        "idempotency_key": "gate_evt_001:ta_001",
        "strategy_lineage_id": "lineage_ema_rsi",
        "strategy_version_id": "strategy_001_v004",
        "order_intent": {"side": "BUY", "instrument_id": "BTCUSDT-PERP.BINANCE", "quantity": "0.01"},
        "risk_decision": {"status": "approved", "risk_profile_id": "risk_paper_default"},
    }


def test_paper_execution_lane_is_decoupled_and_claims_commands_independently() -> None:
    service = ExecutionLaneService()
    profile = service.register_profile(_paper_profile())

    command = service.enqueue_command(_paper_command())
    claimed = service.claim_next(runtime_profile_id=profile.runtime_profile_id, worker_id="exec_worker_1")
    report = service.record_report(
        command_id=claimed.command_id,
        payload={"report_type": "paper_ack", "venue": "SIM", "instrument_id": "BTCUSDT-PERP.BINANCE"},
    )
    snapshot = service.snapshot(runtime_profile_id=profile.runtime_profile_id)

    assert profile.strategy_lane_coupled is False
    assert profile.lane_mode == ExecutionLaneMode.PAPER
    assert command.command_id.startswith("exec_cmd_")
    assert command.may_submit_order is False
    assert claimed.status == ExecutionCommandStatus.CLAIMED
    assert claimed.claimed_by == "exec_worker_1"
    assert report.command_id == claimed.command_id
    assert report.report_type == "paper_ack"
    assert snapshot["queued_commands"] == 0
    assert snapshot["reported_commands"] == 1
    assert snapshot["strategy_lane_coupled"] is False


def test_execution_lane_idempotency_returns_existing_command() -> None:
    service = ExecutionLaneService()
    service.register_profile(_paper_profile())

    first = service.enqueue_command(_paper_command())
    second = service.enqueue_command(_paper_command())

    assert first.command_id == second.command_id
    assert len(service.list_commands(runtime_profile_id="rp_paper_001")) == 1


def test_execution_lane_rejects_strategy_process_coupling_and_secrets() -> None:
    service = ExecutionLaneService()
    service.register_profile(_paper_profile())

    coupled = _paper_command()
    coupled["strategy_runtime_id"] = "strategy_process_123"
    with pytest.raises(ValueError, match="strategy lane coupling"):
        service.enqueue_command(coupled)

    secret = _paper_command()
    secret["idempotency_key"] = "gate_evt_001:secret"
    secret["order_intent"] = {"side": "BUY", "api_key": "should-not-be-here"}
    with pytest.raises(ValueError, match="credentials"):
        service.enqueue_command(secret)


def test_live_command_requires_explicit_live_profile_and_all_gates() -> None:
    service = ExecutionLaneService()
    service.register_profile(
        {
            "tenant_id": "tenant_a",
            "project_id": "project_alpha",
            "runtime_profile_id": "rp_live_disabled",
            "profile_name": "Disabled live lane",
            "lane_mode": "live",
            "enabled": False,
            "adapter_id": "BINANCE_PERP",
            "venue": "BINANCE",
            "consumes_stream": "builder.execution.commands.live.project_alpha",
        }
    )

    live_command = {
        **_paper_command(),
        "runtime_profile_id": "rp_live_disabled",
        "lane_mode": "live",
        "idempotency_key": "live:ta_001",
        "live_trading_enabled": True,
        "execution_authority": True,
        "may_submit_order": True,
        "promotion_approval_id": "approval_001",
        "risk_profile_id": "risk_live_001",
        "credential_slot_ref": "credslot://server/binance_main",
        "risk_decision": {"status": "approved", "risk_profile_id": "risk_live_001"},
    }

    with pytest.raises(ValueError, match="profile is not live-enabled"):
        service.enqueue_command(live_command)


def test_live_command_can_be_queued_only_with_profile_authority_and_risk_approval() -> None:
    service = ExecutionLaneService()
    service.register_profile(
        {
            "tenant_id": "tenant_a",
            "project_id": "project_alpha",
            "runtime_profile_id": "rp_live_001",
            "profile_name": "Live execution lane",
            "lane_mode": "live",
            "enabled": True,
            "adapter_id": "BINANCE_PERP",
            "venue": "BINANCE",
            "venue_account_id": "MAIN-BINANCE-001",
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
            "consumes_stream": "builder.execution.commands.live.project_alpha",
        }
    )

    command = service.enqueue_command(
        {
            **_paper_command(),
            "runtime_profile_id": "rp_live_001",
            "lane_mode": "live",
            "idempotency_key": "live:ta_002",
            "live_trading_enabled": True,
            "execution_authority": True,
            "may_submit_order": True,
            "promotion_approval_id": "approval_001",
            "risk_profile_id": "risk_live_001",
            "credential_slot_ref": "credslot://server/binance_main",
            "adapter_id": "BINANCE_PERP",
            "venue": "BINANCE",
            "venue_account_id": "MAIN-BINANCE-001",
            "risk_decision": {"status": "approved", "risk_profile_id": "risk_live_001"},
        }
    )

    assert command.lane_mode == ExecutionLaneMode.LIVE
    assert command.may_submit_order is True
    assert command.strategy_lane_coupled is False


def test_execution_lane_worker_scaffold_has_no_strategy_imports() -> None:
    worker = __import__("pathlib").Path("services/workers/execution_lane_worker.py").read_text()

    assert "packages.strategy" not in worker
    assert "nautilus_rule_graph.strategy" not in worker
    assert "strategy_lane_coupled" in worker
