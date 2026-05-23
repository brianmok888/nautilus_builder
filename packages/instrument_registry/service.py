from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from packages.adapter_registry.service import AdapterRegistryService


class InstrumentSelection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    instrument_id: str
    market_type: str
    supported_data_types: list[str]
    supported_timeframes: list[str]
    available_date_ranges: list[str]


_INSTRUMENTS: dict[str, dict[str, InstrumentSelection]] = {
    "BINANCE_PERP": {
        "BTCUSDT-PERP": InstrumentSelection(
            instrument_id="BTCUSDT-PERP",
            market_type="crypto_perp",
            supported_data_types=["historical_bars", "funding", "liquidation"],
            supported_timeframes=["1m", "5m", "1h"],
            available_date_ranges=["2024-01-01:2024-03-01", "2024-03-01:2024-06-01"],
        )
    },
    "DATABENTO_US_EQUITY": {
        "AAPL": InstrumentSelection(
            instrument_id="AAPL",
            market_type="equity",
            supported_data_types=["historical_bars", "trade_ticks"],
            supported_timeframes=["1m", "1h", "1d"],
            available_date_ranges=["2024-01-01:2024-03-01"],
        )
    },
}


class InstrumentRegistryService:
    def __init__(self) -> None:
        self._adapters = AdapterRegistryService()

    def validate_selection(
        self,
        *,
        adapter_id: str,
        instrument_id: str,
        data_type: str,
        timeframe: str,
        market_type: str,
        date_range: str,
    ) -> InstrumentSelection:
        profile = self._adapters.get_adapter_profile(adapter_id)
        if data_type not in profile.data_modes:
            raise ValueError(f"requested data type unsupported: {data_type}")

        supported = _INSTRUMENTS.get(adapter_id, {})
        instrument = supported.get(instrument_id)
        if instrument is None:
            raise ValueError(f"instrument unknown for adapter {adapter_id}: {instrument_id}")

        if instrument.market_type != market_type:
            raise ValueError(
                f"market type mismatched for {instrument_id}: expected {instrument.market_type}, got {market_type}"
            )

        if timeframe not in instrument.supported_timeframes:
            raise ValueError(f"date range unavailable or unsupported timeframe: {timeframe}")

        if date_range not in instrument.available_date_ranges:
            raise ValueError(f"date range unavailable: {date_range}")

        return instrument

    def search_instruments(self, *, adapter_id: str, query: str) -> list[InstrumentSelection]:
        self._adapters.get_adapter_profile(adapter_id)
        normalized = query.upper()
        return [
            instrument
            for instrument_id, instrument in _INSTRUMENTS.get(adapter_id, {}).items()
            if normalized in instrument_id.upper()
        ]

    def data_availability(self, *, adapter_id: str, instrument_id: str) -> InstrumentSelection:
        self._adapters.get_adapter_profile(adapter_id)
        instrument = _INSTRUMENTS.get(adapter_id, {}).get(instrument_id)
        if instrument is None:
            raise ValueError(f"instrument unknown for adapter {adapter_id}: {instrument_id}")
        return instrument
