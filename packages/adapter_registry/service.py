from __future__ import annotations

from packages.adapter_registry.models import AdapterProfile


_ADAPTERS: dict[str, AdapterProfile] = {
    "BINANCE_PERP": AdapterProfile(
        adapter_id="BINANCE_PERP",
        enabled=True,
        venue="BINANCE",
        asset_class="crypto_perp",
        data_modes=[
            "historical_bars",
            "trade_ticks",
            "quote_ticks",
            "order_book_delta",
            "funding",
            "liquidation",
        ],
        execution_modes={"backtest": True, "paper": False, "live": False},
    ),
    "DATABENTO_US_EQUITY": AdapterProfile(
        adapter_id="DATABENTO_US_EQUITY",
        enabled=True,
        venue="DATABENTO",
        asset_class="equity",
        data_modes=["historical_bars", "trade_ticks", "quote_ticks"],
        execution_modes={"backtest": True, "paper": False, "live": False},
    ),
    "KRAKEN_SPOT": AdapterProfile(
        adapter_id="KRAKEN_SPOT",
        enabled=False,
        venue="KRAKEN",
        asset_class="crypto_spot",
        data_modes=["historical_bars"],
        execution_modes={"backtest": False, "paper": False, "live": False},
    ),
}


class AdapterRegistryService:
    def get_adapter_profile(self, adapter_id: str) -> AdapterProfile:
        profile = _ADAPTERS.get(adapter_id)
        if profile is None:
            raise ValueError(f"unknown adapter: {adapter_id}")
        if not profile.enabled:
            raise ValueError(f"adapter disabled: {adapter_id}")
        return profile
