from __future__ import annotations

from services.api.app import create_app


def test_backtest_profile_validation_accepts_supported_market_selection() -> None:
    response = create_app().post(
        "/api/backtest-profiles/validate",
        json={
            "adapter_id": "BINANCE_PERP",
            "instrument_id": "BTCUSDT-PERP",
            "data_type": "historical_bars",
            "timeframe": "1m",
            "market_type": "crypto_perp",
            "date_range": "2024-01-01:2024-03-01",
        },
    )

    assert response.status_code == 200
    assert response.json()["valid"] is True
    assert response.json()["instrument"]["instrument_id"] == "BTCUSDT-PERP"


def test_backtest_profile_validation_rejects_invalid_selection() -> None:
    response = create_app().post(
        "/api/backtest-profiles/validate",
        json={
            "adapter_id": "BINANCE_PERP",
            "instrument_id": "BTCUSDT-PERP",
            "data_type": "historical_bars",
            "timeframe": "1d",
            "market_type": "crypto_perp",
            "date_range": "2024-01-01:2024-03-01",
        },
    )

    assert response.status_code == 422
    assert response.json()["valid"] is False
