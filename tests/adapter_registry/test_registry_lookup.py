from __future__ import annotations

from packages.adapter_registry.service import AdapterRegistryService


def test_supported_adapter_lookup_returns_profile() -> None:
    service = AdapterRegistryService()

    profile = service.get_adapter_profile("BINANCE_PERP")

    assert profile.adapter_id == "BINANCE_PERP"
    assert profile.enabled is True
    assert profile.venue == "BINANCE"
    assert "historical_bars" in profile.data_modes
    assert profile.execution_modes["backtest"] is True


def test_disabled_adapter_is_rejected() -> None:
    service = AdapterRegistryService()

    error = None
    try:
        service.get_adapter_profile("KRAKEN_SPOT")
    except ValueError as exc:
        error = str(exc)

    assert error is not None
    assert "disabled" in error


def test_unknown_adapter_is_rejected() -> None:
    service = AdapterRegistryService()

    error = None
    try:
        service.get_adapter_profile("my_module.SomeLiveAdapterClass")
    except ValueError as exc:
        error = str(exc)

    assert error is not None
    assert "unknown adapter" in error.lower()
