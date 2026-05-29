"""Seed Postgres with default adapter and instrument data."""
from __future__ import annotations

from typing import Any

from packages.adapter_registry.models import AdapterProfile
from packages.instrument_registry.service import InstrumentSelection
from packages.postgres.adapter_repository import PostgresAdapterRepository


DEFAULT_ADAPTERS: list[AdapterProfile] = [
    AdapterProfile(
        adapter_id="BINANCE_PERP",
        enabled=True,
        venue="BINANCE",
        asset_class="crypto_perp",
        data_modes=["historical_bars", "trade_ticks", "quote_ticks", "order_book_delta", "funding", "liquidation"],
        execution_modes={"backtest": True, "paper": False, "live": False},
    ),
    AdapterProfile(
        adapter_id="DATABENTO_US_EQUITY",
        enabled=True,
        venue="DATABENTO",
        asset_class="equity",
        data_modes=["historical_bars", "trade_ticks", "quote_ticks"],
        execution_modes={"backtest": True, "paper": False, "live": False},
    ),
    AdapterProfile(
        adapter_id="KRAKEN_SPOT",
        enabled=False,
        venue="KRAKEN",
        asset_class="crypto_spot",
        data_modes=["historical_bars"],
        execution_modes={"backtest": False, "paper": False, "live": False},
    ),
]

DEFAULT_INSTRUMENTS: dict[str, list[InstrumentSelection]] = {
    "BINANCE_PERP": [
        InstrumentSelection(
            instrument_id="BTCUSDT-PERP",
            market_type="crypto_perp",
            supported_data_types=["historical_bars", "quote_ticks", "funding", "liquidation"],
            supported_timeframes=["1m", "5m", "1h"],
            available_date_ranges=["2024-01-01:2024-03-01", "2024-03-01:2024-06-01"],
        ),
    ],
    "DATABENTO_US_EQUITY": [
        InstrumentSelection(
            instrument_id="AAPL",
            market_type="equity",
            supported_data_types=["historical_bars", "trade_ticks"],
            supported_timeframes=["1m", "1h", "1d"],
            available_date_ranges=["2024-01-01:2024-03-01"],
        ),
    ],
}


def seed_default_market_data(conn: Any, schema: str = "builder") -> None:
    """Upsert default adapters and instruments into Postgres."""
    repo = PostgresAdapterRepository(conn, schema=schema)
    for adapter in DEFAULT_ADAPTERS:
        repo.upsert_adapter(adapter)
    for adapter_id, instruments in DEFAULT_INSTRUMENTS.items():
        for instrument in instruments:
            repo.upsert_instrument(adapter_id, instrument)
