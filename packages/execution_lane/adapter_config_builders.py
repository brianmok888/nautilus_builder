from __future__ import annotations

from typing import Any, Protocol

from .models import ExecutionLaneCommand, ExecutionLaneProfile


class AdapterClientConfigBuilder(Protocol):
    def __call__(
        self,
        *,
        profile: ExecutionLaneProfile,
        command: ExecutionLaneCommand,
        credential_values: dict[str, str],
    ) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
        """Return (data_clients, exec_clients, data_factories, exec_factories)."""
        ...


def binance_client_config_builder(
    *,
    profile: ExecutionLaneProfile,
    command: ExecutionLaneCommand,
    credential_values: dict[str, str],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    from nautilus_trader.adapters.binance.common.enums import BinanceAccountType
    from nautilus_trader.adapters.binance.config import BinanceDataClientConfig, BinanceExecClientConfig, BinanceInstrumentProviderConfig
    from nautilus_trader.adapters.binance.factories import BinanceLiveDataClientFactory, BinanceLiveExecClientFactory
    from nautilus_trader.model.identifiers import InstrumentId

    api_key = credential_values.get("BINANCE_API_KEY", "").strip()
    api_secret = credential_values.get("BINANCE_API_SECRET", "").strip()
    if not api_key or not api_secret:
        raise ValueError("BINANCE paper TradingNode session requires BINANCE_API_KEY and BINANCE_API_SECRET")

    instrument_id = str(command.order_intent.get("instrument_id", "")).strip()
    load_ids = frozenset({InstrumentId.from_str(instrument_id)}) if instrument_id else None
    instrument_provider = BinanceInstrumentProviderConfig(load_ids=load_ids)
    adapter_hint = f"{profile.adapter_id or ''} {instrument_id}".upper()
    account_type = (
        BinanceAccountType.USDT_FUTURES
        if any(token in adapter_hint for token in ("PERP", "FUTURE", "FUTURES"))
        else BinanceAccountType.SPOT
    )
    testnet = _truthy(credential_values.get("BINANCE_TESTNET", "true"))
    base_url_http = credential_values.get("BINANCE_BASE_URL")

    data_client = BinanceDataClientConfig(
        api_key=api_key,
        api_secret=api_secret,
        account_type=account_type,
        instrument_provider=instrument_provider,
        testnet=testnet,
        base_url_http=base_url_http,
    )
    exec_client = BinanceExecClientConfig(
        api_key=api_key,
        api_secret=api_secret,
        account_type=account_type,
        instrument_provider=instrument_provider,
        testnet=testnet,
        base_url_http=base_url_http,
    )
    return (
        {"BINANCE": data_client},
        {"BINANCE": exec_client},
        {"BINANCE": BinanceLiveDataClientFactory},
        {"BINANCE": BinanceLiveExecClientFactory},
    )


def generic_client_config_builder(
    *,
    profile: ExecutionLaneProfile,
    command: ExecutionLaneCommand,
    credential_values: dict[str, str],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    from nautilus_trader.live.config import LiveDataClientConfig, LiveExecClientConfig

    venue = (profile.venue or command.venue).upper()
    return ({venue: LiveDataClientConfig()}, {venue: LiveExecClientConfig()}, {}, {})


_ADAPTER_CONFIG_BUILDERS: dict[str, AdapterClientConfigBuilder] = {
    "BINANCE": binance_client_config_builder,
    "BINANCE_PERP": binance_client_config_builder,
}


def get_adapter_config_builder(adapter_id: str) -> AdapterClientConfigBuilder:
    return _ADAPTER_CONFIG_BUILDERS.get(adapter_id.upper(), generic_client_config_builder)


def _truthy(value: object) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "on"}
