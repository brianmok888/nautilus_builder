from __future__ import annotations

from packages.backtest_runner.config_builder import build_backtest_config
from packages.backtest_runner.engine_contract import NAUTILUS_TRADER_VERSION


def test_config_builder_sets_trade_execution_false() -> None:
    config = build_backtest_config(
        strategy_spec_version="0.1.0-draft.1",
        adapter_id="BINANCE_PERP",
        instrument_id="BTCUSDT-PERP",
        compile_hash="abc123",
        validation_report_id="vr_001",
        worker_image="nautilus-builder-worker:dev",
    )
    assert config["trade_execution"] is False, "Builder backtest must be observation-only (trade_execution=False)"
    assert config["live_trading_enabled"] is False
    assert config["execution_authority"] is False


def test_config_builder_includes_pinned_nautilus_version() -> None:
    config = build_backtest_config(
        strategy_spec_version="0.1.0-draft.1",
        adapter_id="BINANCE_PERP",
        instrument_id="BTCUSDT-PERP",
        compile_hash="abc123",
        validation_report_id="vr_001",
        worker_image="nautilus-builder-worker:dev",
    )
    assert config["nautilus_trader_version"] == NAUTILUS_TRADER_VERSION


def test_config_builder_rejects_empty_credentials() -> None:
    import pytest

    config = build_backtest_config(
        strategy_spec_version="0.1.0-draft.1",
        adapter_id="BINANCE_PERP",
        instrument_id="BTCUSDT-PERP",
        compile_hash="abc123",
        validation_report_id="vr_001",
        worker_image="nautilus-builder-worker:dev",
        credentials={},
    )
    assert config["trade_execution"] is False
