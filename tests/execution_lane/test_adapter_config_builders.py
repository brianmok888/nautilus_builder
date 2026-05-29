from __future__ import annotations

import pytest

from packages.execution_lane.adapter_config_builders import (
    binance_client_config_builder,
    generic_client_config_builder,
    get_adapter_config_builder,
)
from packages.execution_lane.models import ExecutionLaneCommand, ExecutionLaneProfile


def _make_profile(adapter_id: str = "BINANCE", venue: str = "BINANCE") -> ExecutionLaneProfile:
    return ExecutionLaneProfile(
        tenant_id="tenant_001",
        project_id="project_001",
        runtime_profile_id="rp_001",
        profile_name="test-profile",
        lane_mode="paper",
        consumes_stream="builder:exec:rp_001",
        enabled=True,
        adapter_id=adapter_id,
        venue=venue,
        paper_trading_enabled=True,
    )


def _make_command(adapter_id: str = "BINANCE", venue: str = "BINANCE") -> ExecutionLaneCommand:
    return ExecutionLaneCommand(
        tenant_id="tenant_001",
        project_id="project_001",
        runtime_profile_id="rp_001",
        lane_mode="paper",
        adapter_id=adapter_id,
        venue=venue,
        trade_action_id="ta_001",
        source_event_id="se_001",
        idempotency_key="ik_001",
        strategy_lineage_id="lineage_001",
        strategy_version_id="sv_001",
        order_intent={"instrument_id": "BTCUSDT-PERP.BINANCE"},
    )


def test_generic_config_builder_raises_on_missing_credentials() -> None:
    """H3: generic fallback must raise a clear error, not silently connect."""
    profile = _make_profile(adapter_id="OKX", venue="OKX")
    command = _make_command(adapter_id="OKX", venue="OKX")
    with pytest.raises(ValueError, match="credential"):
        generic_client_config_builder(
            profile=profile,
            command=command,
            credential_values={},
        )


def test_generic_config_builder_raises_on_empty_credentials() -> None:
    """H3: empty/whitespace credentials must also raise."""
    profile = _make_profile(adapter_id="KRAKEN", venue="KRAKEN")
    command = _make_command(adapter_id="KRAKEN", venue="KRAKEN")
    with pytest.raises(ValueError, match="credential"):
        generic_client_config_builder(
            profile=profile,
            command=command,
            credential_values={"KRAKEN_API_KEY": "  ", "KRAKEN_API_SECRET": ""},
        )


def test_get_adapter_config_builder_returns_generic_for_unknown() -> None:
    builder = get_adapter_config_builder("UNKNOWN_VENUE")
    assert builder is generic_client_config_builder


def test_get_adapter_config_builder_returns_binance_for_binance_perp() -> None:
    builder = get_adapter_config_builder("BINANCE_PERP")
    assert builder is binance_client_config_builder


def test_get_adapter_config_builder_returns_binance_for_binance() -> None:
    builder = get_adapter_config_builder("BINANCE")
    assert builder is binance_client_config_builder
