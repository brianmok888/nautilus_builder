"""Test that execution lane validates adapters against the adapter registry."""
from __future__ import annotations

from packages.execution_lane.models import ExecutionLaneCommand, ExecutionLaneMode, ExecutionLaneProfile
from packages.execution_lane.sessions import _client_configs


def _make_profile(adapter_id: str = "BINANCE_PERP", venue: str = "BINANCE") -> ExecutionLaneProfile:
    return ExecutionLaneProfile(
        tenant_id="tenant_001",
        project_id="project_001",
        runtime_profile_id="rp_001",
        profile_name="Test Profile",
        lane_mode=ExecutionLaneMode.PAPER,
        enabled=True,
        consumes_stream="exec_lane_events",
        adapter_id=adapter_id,
        venue=venue,
        paper_trading_enabled=True,
    )


def _make_command(adapter_id: str = "BINANCE_PERP", venue: str = "BINANCE") -> ExecutionLaneCommand:
    return ExecutionLaneCommand(
        command_id="cmd_001",
        runtime_profile_id="rp_001",
        tenant_id="tenant_001",
        project_id="project_001",
        lane_mode=ExecutionLaneMode.PAPER,
        adapter_id=adapter_id,
        venue=venue,
        strategy_lineage_id="sl_001",
        strategy_version_id="sv_001",
        trade_action_id="ta_001",
        source_event_id="se_001",
        idempotency_key="ik_001",
        order_intent={"instrument_id": "BTCUSDT-PERP.BINANCE"},
        risk_decision={"status": "approved"},
    )


def test_registered_adapter_builds_client_configs() -> None:
    """Known, enabled adapter (BINANCE_PERP) resolves through adapter registry + builder."""
    profile = _make_profile()
    command = _make_command()
    creds = {"BINANCE_API_KEY": "test_key", "BINANCE_API_SECRET": "test_secret"}

    data_clients, exec_clients, data_factories, exec_factories = _client_configs(
        profile=profile, command=command, credential_values=creds,
    )
    assert "BINANCE" in data_clients
    assert "BINANCE" in exec_clients


def test_unregistered_adapter_raises_on_missing_credentials() -> None:
    """Unknown adapter_id with no credentials raises a clear ValueError."""
    import pytest
    profile = _make_profile(adapter_id="UNKNOWN_VENUE", venue="UNKNOWN_VENUE")
    command = _make_command(adapter_id="UNKNOWN_VENUE", venue="UNKNOWN_VENUE")
    creds: dict[str, str] = {}

    with pytest.raises(ValueError, match="credential"):
        _client_configs(
            profile=profile, command=command, credential_values=creds,
        )


def test_disabled_adapter_raises_on_missing_credentials() -> None:
    """Disabled adapter (KRAKEN_SPOT) with no credentials raises ValueError."""
    import pytest
    profile = _make_profile(adapter_id="KRAKEN_SPOT", venue="KRAKEN")
    command = _make_command(adapter_id="KRAKEN_SPOT", venue="KRAKEN")
    creds: dict[str, str] = {}

    with pytest.raises(ValueError, match="credential"):
        _client_configs(
            profile=profile, command=command, credential_values=creds,
        )
