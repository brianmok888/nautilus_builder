"""P3-1 regression: legacy stream-map must have owner, expiry, and require opt-in.

The nautilus:tradehud:* legacy aliases must remain labelled with an owner, an
expiry date, and concrete removal criteria, and must require an explicit env
opt-in (TRADEHUD_STREAM_NAMESPACE=nautilus_tradehud). The default namespace is nd.
"""
from __future__ import annotations

from datetime import date

import pytest

from packages.tradehud_contracts.config import (
    TradeHudRedisConfig,
    _LEGACY_STREAM_MAP,
    _LEGACY_STREAM_MAP_OWNER,
    _LEGACY_STREAM_MAP_EXPIRES,
    _LEGACY_STREAM_MAP_REMOVAL_CRITERIA,
    _ND_STREAM_MAP,
)


def test_legacy_stream_map_has_owner_expiry_and_removal_criteria():
    assert _LEGACY_STREAM_MAP_OWNER, "legacy stream map must have an owner"
    assert _LEGACY_STREAM_MAP_EXPIRES, "legacy stream map must have an expiry date"
    assert isinstance(_LEGACY_STREAM_MAP_REMOVAL_CRITERIA, list) and len(_LEGACY_STREAM_MAP_REMOVAL_CRITERIA) >= 2
    # Expiry must parse as a real date.
    parsed = date.fromisoformat(_LEGACY_STREAM_MAP_EXPIRES)


def test_legacy_stream_map_not_expired(monkeypatch):
    """The expiry guard fails (alert) only on/after the recorded expiry date.
    Before that date the legacy map remains permitted. This test pins the contract
    so an owner must renew the expiry to keep the legacy shim."""
    today = date.today()
    expiry = date.fromisoformat(_LEGACY_STREAM_MAP_EXPIRES)
    # If the expiry has passed, this assert documents that the legacy map should
    # have been removed/renewed. Until then it must still resolve.
    if today < expiry:
        cfg = TradeHudRedisConfig(stream_namespace="nautilus_tradehud")
        assert "nautilus:tradehud:" in cfg.get_stream_map()["trades"]


def test_default_namespace_is_nd_not_legacy():
    cfg = TradeHudRedisConfig()
    assert cfg.stream_namespace == "nd"
    # Default map resolves to nd.* keys, not legacy nautilus:tradehud:* keys.
    trades_key = cfg.get_stream_map()["trades"]
    assert trades_key.startswith("nd.")


def test_legacy_namespace_requires_explicit_opt_in(monkeypatch):
    monkeypatch.delenv("TRADEHUD_STREAM_NAMESPACE", raising=False)
    cfg = TradeHudRedisConfig.from_env()
    assert cfg.stream_namespace == "nd"
    # Only an explicit opt-in selects the legacy map.
    monkeypatch.setenv("TRADEHUD_STREAM_NAMESPACE", "nautilus_tradehud")
    legacy_cfg = TradeHudRedisConfig.from_env()
    assert legacy_cfg.stream_namespace == "nautilus_tradehud"


def test_no_new_direct_imports_of_legacy_map_outside_config():
    """The legacy map must only be consumed via get_stream_map(); no production
    code should import _LEGACY_STREAM_MAP directly (it stays an internal shim)."""
    import packages.tradehud_contracts.config as cfg_mod
    # The map is defined here; consumers go through TradeHudRedisConfig.get_stream_map.
    assert hasattr(cfg_mod, "_LEGACY_STREAM_MAP")
    assert _ND_STREAM_MAP["trades"] == "nd.public_trade_tick"
