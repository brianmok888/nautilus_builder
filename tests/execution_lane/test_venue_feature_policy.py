from __future__ import annotations

import pytest

from packages.execution_lane import ExecutionLaneService


def _venue_profile() -> dict[str, object]:
    return {
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
    }


def _venue_command() -> dict[str, object]:
    return {
        "tenant_id": "tenant_a",
        "project_id": "project_alpha",
        "runtime_profile_id": "rp_paper_binance",
        "lane_mode": "paper",
        "adapter_id": "BINANCE_PERP",
        "venue": "BINANCE",
        "venue_account_id": "SIM-BINANCE-001",
        "trade_action_id": "ta_binance_001",
        "source_event_id": "gate_evt_binance_001",
        "idempotency_key": "gate_evt_binance_001:ta_binance_001",
        "strategy_lineage_id": "lineage_ema_rsi",
        "strategy_version_id": "strategy_001_v004",
        "order_intent": {"side": "BUY", "instrument_id": "BTCUSDT-PERP.BINANCE", "quantity": "0.01"},
        "risk_decision": {"status": "approved", "risk_profile_id": "risk_paper_default"},
    }


def test_execution_lane_profile_and_commands_bind_to_venue_and_expose_ui_features() -> None:
    service = ExecutionLaneService()
    profile = service.register_profile(_venue_profile())
    command = service.enqueue_command(_venue_command())
    snapshot = service.snapshot(runtime_profile_id=profile.runtime_profile_id)

    assert profile.adapter_id == "BINANCE_PERP"
    assert profile.venue == "BINANCE"
    assert command.adapter_id == "BINANCE_PERP"
    assert command.venue == "BINANCE"
    assert snapshot["venue_bindings"] == [
        {
            "runtime_profile_id": "rp_paper_binance",
            "adapter_id": "BINANCE_PERP",
            "venue": "BINANCE",
            "venue_account_id": "SIM-BINANCE-001",
            "lane_mode": "paper",
            "enabled": True,
        }
    ]
    assert snapshot["ui_features"] == {
        "execution_lane_ui_enabled": True,
        "paper_controls_enabled": True,
        "live_controls_enabled": False,
        "credential_inputs_allowed": False,
        "strategy_lane_coupled": False,
    }


def test_enabled_execution_lane_profile_requires_adapter_and_venue() -> None:
    service = ExecutionLaneService()
    payload = _venue_profile()
    payload.pop("adapter_id")

    with pytest.raises(ValueError, match="adapter_id"):
        service.register_profile(payload)

    payload = _venue_profile()
    payload["venue"] = ""
    with pytest.raises(ValueError, match="venue"):
        service.register_profile(payload)


def test_execution_lane_rejects_command_for_wrong_venue() -> None:
    service = ExecutionLaneService()
    service.register_profile(_venue_profile())
    command = _venue_command()
    command["venue"] = "OKX"

    with pytest.raises(ValueError, match="venue does not match"):
        service.enqueue_command(command)


def test_live_ui_controls_require_live_authority() -> None:
    service = ExecutionLaneService()
    profile = {
        **_venue_profile(),
        "runtime_profile_id": "rp_live_ui_denied",
        "profile_name": "Live UI denied",
        "lane_mode": "live",
        "paper_trading_enabled": False,
        "live_controls_enabled": True,
        "consumes_stream": "builder.execution.commands.live.project_alpha.binance",
    }

    with pytest.raises(ValueError, match="live UI controls require live authority"):
        service.register_profile(profile)
