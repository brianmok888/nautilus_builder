from __future__ import annotations

from services.api.app import create_app


def test_market_catalog_supports_query_friendly_instrument_lookup() -> None:
    response = create_app().get("/api/instruments?adapter_id=BINANCE_PERP&query=BTC")

    assert response.status_code == 200
    assert response.json()[0]["instrument_id"] == "BTCUSDT-PERP"


def test_adapters_endpoint_lists_only_backend_approved_profiles() -> None:
    response = create_app().get("/api/adapters")

    payload = response.json()
    assert response.status_code == 200
    assert [adapter["adapter_id"] for adapter in payload] == ["BINANCE_PERP", "DATABENTO_US_EQUITY"]
    assert all(adapter["execution_modes"]["live"] is False for adapter in payload)


def test_instruments_endpoint_filters_by_adapter_and_query() -> None:
    response = create_app().get("/api/instruments/BINANCE_PERP/BTC")

    payload = response.json()
    assert response.status_code == 200
    assert payload[0]["instrument_id"] == "BTCUSDT-PERP"
    assert "liquidation" in payload[0]["supported_data_types"]


def test_data_availability_endpoint_exposes_backend_registry_data() -> None:
    response = create_app().get("/api/data-availability/BINANCE_PERP/BTCUSDT-PERP")

    payload = response.json()
    assert response.status_code == 200
    assert payload["supported_timeframes"] == ["1m", "5m", "1h"]
    assert payload["available_date_ranges"]
