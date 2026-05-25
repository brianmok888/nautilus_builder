from __future__ import annotations

from pathlib import Path
from tempfile import mkdtemp
from typing import Any

from .engine_contract import NAUTILUS_TRADER_VERSION
from .runtime_check import assert_nautilus_runtime_version

CATALOG_BACKED_REPLAY_SMOKE_MODE = "catalog_backed_replay_smoke"
SUBSCRIBE_STRATEGY_PATH = "nautilus_trader.examples.strategies.subscribe:SubscribeStrategy"
SUBSCRIBE_STRATEGY_CONFIG_PATH = "nautilus_trader.examples.strategies.subscribe:SubscribeStrategyConfig"


def run_catalog_backed_nautilus_replay_smoke(*, catalog_path: str | Path | None = None) -> dict[str, object]:
    """Run a deterministic catalog-backed NautilusTrader replay smoke.

    The smoke writes synthetic historical quote ticks to a ``ParquetDataCatalog``
    and runs NautilusTrader's high-level ``BacktestNode`` with an official
    no-order subscribe strategy. It proves catalog data is replayed by the
    pinned Nautilus runtime while preserving Builder's no-live-order boundary.
    """

    status = assert_nautilus_runtime_version()

    from nautilus_trader.backtest.node import BacktestNode
    from nautilus_trader.config import BacktestDataConfig
    from nautilus_trader.config import BacktestEngineConfig
    from nautilus_trader.config import BacktestRunConfig
    from nautilus_trader.config import BacktestVenueConfig
    from nautilus_trader.config import ImportableStrategyConfig
    from nautilus_trader.config import LoggingConfig
    from nautilus_trader.model.data import QuoteTick
    from nautilus_trader.persistence.catalog.parquet import ParquetDataCatalog
    from nautilus_trader.persistence.catalog.singleton import clear_singleton_instances
    from nautilus_trader.test_kit.stubs.data import TestDataStubs
    from nautilus_trader.test_kit.stubs.data import TestInstrumentProvider

    resolved_catalog_path = Path(catalog_path) if catalog_path is not None else Path(mkdtemp(prefix="nautilus_builder_replay_")) / "catalog"
    resolved_catalog_path.mkdir(parents=True, exist_ok=True)

    clear_singleton_instances(ParquetDataCatalog)
    catalog = ParquetDataCatalog(path=resolved_catalog_path.as_posix())

    instrument = TestInstrumentProvider.default_fx_ccy("AUD/USD")
    ticks = [
        TestDataStubs.quote_tick(
            instrument=instrument,
            bid_price=1.00000 + index * 0.00010,
            ask_price=1.00020 + index * 0.00010,
            bid_size=1_000_000,
            ask_size=1_000_000,
            ts_event=(index + 1) * 1_000_000_000,
            ts_init=(index + 1) * 1_000_000_000,
        )
        for index in range(5)
    ]

    catalog.write_data([instrument])
    catalog.write_data(ticks)
    catalog_data_count = len(catalog.quote_ticks(instrument_ids=[str(instrument.id)]))

    strategy = ImportableStrategyConfig(
        strategy_path=SUBSCRIBE_STRATEGY_PATH,
        config_path=SUBSCRIBE_STRATEGY_CONFIG_PATH,
        config={"instrument_id": instrument.id, "quote_ticks": True},
    )
    engine = BacktestEngineConfig(
        logging=LoggingConfig(log_level="ERROR", bypass_logging=True, log_colors=False, print_config=False),
        strategies=[strategy],
    )
    run_config = BacktestRunConfig(
        engine=engine,
        venues=[
            BacktestVenueConfig(
                name=str(instrument.venue),
                oms_type="NETTING",
                account_type="MARGIN",
                base_currency="USD",
                starting_balances=["1000000 USD"],
            )
        ],
        data=[
            BacktestDataConfig(
                catalog_path=resolved_catalog_path.as_posix(),
                data_cls=QuoteTick.fully_qualified_name(),
                instrument_id=instrument.id,
            )
        ],
    )

    results = BacktestNode(configs=[run_config]).run()
    if len(results) != 1:
        raise RuntimeError(f"expected one Nautilus backtest result, got {len(results)}")
    result = results[0]

    metric_sections = _present_metric_sections(result)
    return {
        "engine_mode": CATALOG_BACKED_REPLAY_SMOKE_MODE,
        "nautilus_trader_version": status.installed_version or NAUTILUS_TRADER_VERSION,
        "catalog_backed": True,
        "catalog_path": resolved_catalog_path.as_posix(),
        "data_cls": QuoteTick.fully_qualified_name(),
        "instrument_id": str(instrument.id),
        "strategy_path": SUBSCRIBE_STRATEGY_PATH,
        "catalog_data_count": catalog_data_count,
        "iterations": int(result.iterations),
        "backtest_start": int(result.backtest_start),
        "backtest_end": int(result.backtest_end),
        "run_finished": result.run_finished is not None,
        "metrics_present": bool(metric_sections),
        "metric_sections": metric_sections,
        "orders": int(result.total_orders),
        "positions": int(result.total_positions),
        "live_trading_enabled": False,
        "execution_authority": False,
        "credentials_used": False,
    }


def _present_metric_sections(result: Any) -> list[str]:
    sections: list[str] = []
    if getattr(result, "stats_pnls", None) is not None:
        sections.append("stats_pnls")
    if getattr(result, "stats_returns", None) is not None:
        sections.append("stats_returns")
    return sections
