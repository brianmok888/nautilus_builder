from __future__ import annotations

from packages.instrument_registry.service import InstrumentRegistryService


def test_supported_instrument_lookup_passes() -> None:
    service = InstrumentRegistryService()

    instrument = service.validate_selection(
        adapter_id="BINANCE_PERP",
        instrument_id="BTCUSDT-PERP",
        data_type="historical_bars",
        timeframe="1h",
        market_type="crypto_perp",
        date_range="2024-01-01:2024-03-01",
    )

    assert instrument.instrument_id == "BTCUSDT-PERP"
    assert instrument.market_type == "crypto_perp"
    assert instrument.supported_timeframes == ["1m", "5m", "1h"]


def test_invalid_adapter_instrument_combination_fails() -> None:
    service = InstrumentRegistryService()

    error = None
    try:
        service.validate_selection(
            adapter_id="DATABENTO_US_EQUITY",
            instrument_id="BTCUSDT-PERP",
            data_type="historical_bars",
            timeframe="1h",
            market_type="equity",
            date_range="2024-01-01:2024-03-01",
        )
    except ValueError as exc:
        error = str(exc)

    assert error is not None
    assert "instrument unknown" in error.lower() or "mismatched" in error.lower()


def test_unsupported_timeframe_fails() -> None:
    service = InstrumentRegistryService()

    error = None
    try:
        service.validate_selection(
            adapter_id="BINANCE_PERP",
            instrument_id="BTCUSDT-PERP",
            data_type="historical_bars",
            timeframe="4h",
            market_type="crypto_perp",
            date_range="2024-01-01:2024-03-01",
        )
    except ValueError as exc:
        error = str(exc)

    assert error is not None
    assert "unsupported" in error.lower() or "unavailable" in error.lower()
