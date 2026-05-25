from __future__ import annotations

import hashlib
import json
from pathlib import Path
from tempfile import mkdtemp
from typing import Any

from packages.auth import UserProjectContext, assert_same_project
from packages.catalog_datasets import CatalogDataset, CatalogPathPolicy
from packages.strategy_compiler.compiler import compile_strategy_spec
from packages.strategy_spec.models import StrategySpec

from .engine_contract import NAUTILUS_TRADER_VERSION
from .runtime_check import assert_nautilus_runtime_version

STRATEGY_SPEC_CATALOG_REPLAY_MODE = "strategy_spec_catalog_replay"
STRATEGY_SPEC_SYNTHETIC_CATALOG_SMOKE_MODE = "strategy_spec_synthetic_catalog_smoke"
STRATEGY_SPEC_REPLAY_DATA_TYPE = "quote_ticks"
USER_CATALOG_DATASET_SOURCE = "user_catalog"
SYNTHETIC_TEST_KIT_DATASET_SOURCE = "synthetic_test_kit"
RULE_GRAPH_STRATEGY_PATH = "packages.nautilus_rule_graph.strategy:RuleGraphBacktestStrategy"
RULE_GRAPH_STRATEGY_CONFIG_PATH = "packages.nautilus_rule_graph.strategy:RuleGraphBacktestStrategyConfig"


def run_strategy_spec_catalog_replay(
    *,
    strategy_spec_payload: dict[str, Any],
    dataset: CatalogDataset,
    context: UserProjectContext,
    catalog_root: str | Path | None = None,
) -> dict[str, object]:
    """Run a read-only user-catalog Nautilus replay using a Builder StrategySpec strategy."""

    assert_same_project(context, dataset.scoped_artifact)
    status = assert_nautilus_runtime_version()
    spec = StrategySpec.model_validate(strategy_spec_payload)
    compile_artifact = compile_strategy_spec(spec.model_dump(mode="json"), profile="backtest")
    _assert_dataset_matches_spec(dataset, spec)

    from nautilus_trader.model.data import QuoteTick
    from nautilus_trader.persistence.catalog.parquet import ParquetDataCatalog
    from nautilus_trader.persistence.catalog.singleton import clear_singleton_instances
    from nautilus_trader.test_kit.stubs.data import TestInstrumentProvider

    catalog_path = _resolve_catalog_path(dataset.catalog_path, catalog_root=catalog_root)
    if not catalog_path.exists():
        raise ValueError("user catalog does not exist")
    if not catalog_path.is_dir():
        raise ValueError("user catalog path must be a directory")

    instrument = _instrument_for_builder_id(dataset.instrument_id, TestInstrumentProvider)
    clear_singleton_instances(ParquetDataCatalog)
    catalog = ParquetDataCatalog(path=catalog_path.as_posix())
    catalog_data_count = len(catalog.quote_ticks(instrument_ids=[str(instrument.id)]))
    if catalog_data_count <= 0:
        raise ValueError("user catalog has no matching quote_ticks")

    manifest = _catalog_manifest(catalog_path)
    return _run_strategy_spec_backtest(
        status=status,
        dataset=dataset,
        spec=spec,
        compile_hash=compile_artifact.compile_hash,
        catalog_path=catalog_path,
        data_cls=QuoteTick.fully_qualified_name(),
        instrument=instrument,
        catalog_data_count=catalog_data_count,
        engine_mode=STRATEGY_SPEC_CATALOG_REPLAY_MODE,
        dataset_source=USER_CATALOG_DATASET_SOURCE,
        manifest=manifest,
    )


def run_strategy_spec_synthetic_catalog_smoke(
    *,
    strategy_spec_payload: dict[str, Any],
    dataset: CatalogDataset,
    context: UserProjectContext,
    catalog_root: str | Path | None = None,
) -> dict[str, object]:
    """Write deterministic test-kit data to a controlled catalog and run StrategySpec replay smoke."""

    assert_same_project(context, dataset.scoped_artifact)
    status = assert_nautilus_runtime_version()
    spec = StrategySpec.model_validate(strategy_spec_payload)
    compile_artifact = compile_strategy_spec(spec.model_dump(mode="json"), profile="backtest")
    _assert_dataset_matches_spec(dataset, spec)

    from nautilus_trader.model.data import QuoteTick
    from nautilus_trader.persistence.catalog.parquet import ParquetDataCatalog
    from nautilus_trader.persistence.catalog.singleton import clear_singleton_instances
    from nautilus_trader.test_kit.stubs.data import TestDataStubs
    from nautilus_trader.test_kit.stubs.data import TestInstrumentProvider

    synthetic_root = Path(catalog_root) if catalog_root is not None else Path(mkdtemp(prefix="nautilus_builder_strategy_spec_"))
    catalog_path = _resolve_catalog_path(dataset.catalog_path, catalog_root=synthetic_root)
    catalog_path.mkdir(parents=True, exist_ok=True)
    instrument = _instrument_for_builder_id(dataset.instrument_id, TestInstrumentProvider)

    clear_singleton_instances(ParquetDataCatalog)
    catalog = ParquetDataCatalog(path=catalog_path.as_posix())
    ticks = [
        TestDataStubs.quote_tick(
            instrument=instrument,
            bid_price=50_000.0 + index * 10.0,
            ask_price=50_001.0 + index * 10.0,
            bid_size=1.0,
            ask_size=1.0,
            ts_event=(index + 1) * 1_000_000_000,
            ts_init=(index + 1) * 1_000_000_000,
        )
        for index in range(5)
    ]
    catalog.write_data([instrument])
    catalog.write_data(ticks)
    catalog_data_count = len(catalog.quote_ticks(instrument_ids=[str(instrument.id)]))
    manifest = _catalog_manifest(catalog_path)

    return _run_strategy_spec_backtest(
        status=status,
        dataset=dataset,
        spec=spec,
        compile_hash=compile_artifact.compile_hash,
        catalog_path=catalog_path,
        data_cls=QuoteTick.fully_qualified_name(),
        instrument=instrument,
        catalog_data_count=catalog_data_count,
        engine_mode=STRATEGY_SPEC_SYNTHETIC_CATALOG_SMOKE_MODE,
        dataset_source=SYNTHETIC_TEST_KIT_DATASET_SOURCE,
        manifest=manifest,
    )


def _run_strategy_spec_backtest(
    *,
    status: Any,
    dataset: CatalogDataset,
    spec: StrategySpec,
    compile_hash: str,
    catalog_path: Path,
    data_cls: str,
    instrument: Any,
    catalog_data_count: int,
    engine_mode: str,
    dataset_source: str,
    manifest: dict[str, str],
) -> dict[str, object]:
    from nautilus_trader.backtest.node import BacktestNode
    from nautilus_trader.config import BacktestDataConfig
    from nautilus_trader.config import BacktestEngineConfig
    from nautilus_trader.config import BacktestRunConfig
    from nautilus_trader.config import BacktestVenueConfig
    from nautilus_trader.config import ImportableStrategyConfig
    from nautilus_trader.config import LoggingConfig
    from nautilus_trader.persistence.catalog.parquet import ParquetDataCatalog
    from nautilus_trader.persistence.catalog.singleton import clear_singleton_instances

    clear_singleton_instances(ParquetDataCatalog)
    strategy = ImportableStrategyConfig(
        strategy_path=RULE_GRAPH_STRATEGY_PATH,
        config_path=RULE_GRAPH_STRATEGY_CONFIG_PATH,
        config={
            "instrument_id": instrument.id,
            "strategy_spec": spec.model_dump(mode="json"),
            "compile_hash": compile_hash,
        },
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
                base_currency=None,
                starting_balances=["1000000 USDT"],
            )
        ],
        data=[
            BacktestDataConfig(
                catalog_path=catalog_path.as_posix(),
                data_cls=data_cls,
                instrument_id=instrument.id,
            )
        ],
    )

    results = BacktestNode(configs=[run_config]).run()
    if len(results) != 1:
        raise RuntimeError(f"expected one Nautilus backtest result, got {len(results)}")
    result = results[0]
    return {
        "engine_mode": engine_mode,
        "nautilus_trader_version": status.installed_version or NAUTILUS_TRADER_VERSION,
        "catalog_backed": True,
        "spec_generated": True,
        "dataset_source": dataset_source,
        "dataset_id": dataset.dataset_id,
        "catalog_path": catalog_path.as_posix(),
        "catalog_manifest_checksum": _manifest_checksum(manifest),
        "catalog_manifest_file_count": len(manifest),
        "data_cls": data_cls,
        "builder_instrument_id": dataset.instrument_id,
        "instrument_id": str(instrument.id),
        "strategy_path": RULE_GRAPH_STRATEGY_PATH,
        "strategy_config_path": RULE_GRAPH_STRATEGY_CONFIG_PATH,
        "strategy_spec_version": spec.version,
        "compile_hash": compile_hash,
        "catalog_data_count": catalog_data_count,
        "iterations": int(result.iterations),
        "backtest_start": int(result.backtest_start),
        "backtest_end": int(result.backtest_end),
        "run_finished": result.run_finished is not None,
        "orders": int(result.total_orders),
        "positions": int(result.total_positions),
        "live_trading_enabled": False,
        "execution_authority": False,
        "credentials_used": False,
    }


def _assert_dataset_matches_spec(dataset: CatalogDataset, spec: StrategySpec) -> None:
    expected_date_range = f"{spec.data_range.start}:{spec.data_range.end}"
    expected = {
        "adapter_id": spec.adapter_id,
        "instrument_id": spec.instrument_id,
        "date_range": expected_date_range,
    }
    for field_name, expected_value in expected.items():
        actual_value = getattr(dataset, field_name)
        if actual_value != expected_value:
            raise ValueError(f"dataset field mismatch: {field_name} expected {expected_value}, got {actual_value}")
    if dataset.data_type != STRATEGY_SPEC_REPLAY_DATA_TYPE:
        raise ValueError(f"strategy replay requires {STRATEGY_SPEC_REPLAY_DATA_TYPE} dataset, got {dataset.data_type}")


def _resolve_catalog_path(catalog_path: str | Path, *, catalog_root: str | Path | None) -> Path:
    if catalog_root is None:
        raise ValueError("catalog_root is required for StrategySpec catalog replay")
    return CatalogPathPolicy(catalog_root).validate_path(catalog_path)


def _catalog_manifest(catalog_path: Path) -> dict[str, str]:
    return {
        file.relative_to(catalog_path).as_posix(): hashlib.sha256(file.read_bytes()).hexdigest()
        for file in sorted(catalog_path.rglob("*"))
        if file.is_file()
    }


def _manifest_checksum(manifest: dict[str, str]) -> str:
    encoded = json.dumps(manifest, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _instrument_for_builder_id(builder_instrument_id: str, provider: Any) -> Any:
    if builder_instrument_id == "BTCUSDT-PERP":
        return provider.btcusdt_perp_binance()
    if builder_instrument_id == "BTCUSDT":
        return provider.btcusdt_binance()
    if builder_instrument_id == "AAPL":
        return provider.equity(symbol="AAPL")
    raise ValueError(f"no deterministic Nautilus test instrument for {builder_instrument_id}")
