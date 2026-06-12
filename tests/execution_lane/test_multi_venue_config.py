"""TDD tests for multi-venue adapter config builder support (H-01).

Verifies that get_adapter_config_builder returns a working builder
for any venue, not just BINANCE.
"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from packages.execution_lane.adapter_config_builders import (
    get_adapter_config_builder,
    generic_client_config_builder,
)


def _make_profile(venue="BYBIT", **overrides):
    p = MagicMock()
    p.venue = venue
    for k, v in overrides.items():
        setattr(p, k, v)
    return p


def _make_command(venue="BYBIT", **overrides):
    c = MagicMock()
    c.venue = venue
    for k, v in overrides.items():
        setattr(c, k, v)
    return c


class TestMultiVenueFallback:
    def test_bybit_uses_generic_builder(self):
        builder = get_adapter_config_builder("BYBIT")
        assert builder is generic_client_config_builder

    def test_okx_uses_generic_builder(self):
        builder = get_adapter_config_builder("OKX")
        assert builder is generic_client_config_builder

    def test_binance_uses_dedicated_builder(self):
        builder = get_adapter_config_builder("BINANCE")
        assert builder is not generic_client_config_builder

    def test_generic_builder_returns_configs(self):
        profile = _make_profile(venue="BYBIT")
        command = _make_command(venue="BYBIT")
        creds = {"BYBIT_API_KEY": "test", "BYBIT_API_SECRET": "test"}
        data_clients, exec_clients, data_facts, exec_facts = generic_client_config_builder(
            profile=profile, command=command, credential_values=creds,
        )
        assert "BYBIT" in data_clients
        assert "BYBIT" in exec_clients

    def test_generic_builder_raises_on_missing_credentials(self):
        profile = _make_profile(venue="HYPERLIQUID")
        command = _make_command(venue="HYPERLIQUID")
        with pytest.raises(ValueError, match="credential"):
            generic_client_config_builder(
                profile=profile, command=command, credential_values={},
            )
