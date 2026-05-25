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

from packages.backtest_runner import STRATEGY_SPEC_REPLAY_DATA_TYPE


def test_strategy_spec_replay_data_type_is_visible_and_valid_for_btcusdt_perp() -> None:
    service = InstrumentRegistryService()

    instrument = service.data_availability(adapter_id="BINANCE_PERP", instrument_id="BTCUSDT-PERP")
    validated = service.validate_selection(
        adapter_id="BINANCE_PERP",
        instrument_id="BTCUSDT-PERP",
        data_type=STRATEGY_SPEC_REPLAY_DATA_TYPE,
        timeframe="1m",
        market_type="crypto_perp",
        date_range="2024-01-01:2024-03-01",
    )

    assert STRATEGY_SPEC_REPLAY_DATA_TYPE == "quote_ticks"
    assert STRATEGY_SPEC_REPLAY_DATA_TYPE in instrument.supported_data_types
    assert validated.instrument_id == "BTCUSDT-PERP"


def test_instrument_registry_rejects_adapter_data_mode_not_supported_by_instrument() -> None:
    service = InstrumentRegistryService()

    error = None
    try:
        service.validate_selection(
            adapter_id="BINANCE_PERP",
            instrument_id="BTCUSDT-PERP",
            data_type="order_book_delta",
            timeframe="1m",
            market_type="crypto_perp",
            date_range="2024-01-01:2024-03-01",
        )
    except ValueError as exc:
        error = str(exc)

    assert error == "instrument data type unsupported: order_book_delta"
