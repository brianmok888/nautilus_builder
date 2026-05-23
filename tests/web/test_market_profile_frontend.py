from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_market_profile_components_expose_selection_and_validation_surfaces() -> None:
    panel = (ROOT / "apps" / "web" / "components" / "market" / "MarketProfilePanel.tsx").read_text()

    assert "AdapterSelector" in panel
    assert "InstrumentSearch" in panel
    assert "DataAvailabilityPanel" in panel
    assert "validateBacktestProfile" in panel
    assert "adapter_profile_id" in panel


def test_market_api_client_hides_backend_route_shape() -> None:
    api = (ROOT / "apps" / "web" / "lib" / "api.ts").read_text()

    assert "fetchInstruments" in api
    assert "fetchDataAvailability" in api
    assert "URLSearchParams" in api
    assert "adapter_id" in api
    assert "query" in api
