from __future__ import annotations

from pathlib import Path

import packages.backtest_runner as backtest_runner
from packages.backtest_runner.engine_contract import FIXTURE_ENGINE_MODE, INJECTED_ENGINE_MODE, NAUTILUS_TRADER_VERSION


def test_catalog_backed_nautilus_replay_smoke_processes_historical_data_and_strategy(tmp_path: Path) -> None:
    replay = getattr(backtest_runner, "run_catalog_backed_nautilus_replay_smoke", None)
    assert replay is not None, "catalog-backed replay smoke function is missing"

    mode = getattr(backtest_runner, "CATALOG_BACKED_REPLAY_SMOKE_MODE", None)
    assert mode == "catalog_backed_replay_smoke"

    catalog_path = tmp_path / "catalog"
    result = replay(catalog_path=catalog_path)

    assert result["engine_mode"] == mode
    assert result["engine_mode"] not in {
        FIXTURE_ENGINE_MODE,
        INJECTED_ENGINE_MODE,
        backtest_runner.REAL_NAUTILUS_ENGINE_SMOKE_MODE,
    }
    assert result["nautilus_trader_version"] == NAUTILUS_TRADER_VERSION
    assert result["catalog_backed"] is True
    assert Path(str(result["catalog_path"])).name == "catalog"
    assert catalog_path.exists()
    assert result["data_cls"] == "nautilus_trader.model.data:QuoteTick"
    assert result["strategy_path"] == "nautilus_trader.examples.strategies.subscribe:SubscribeStrategy"
    assert result["catalog_data_count"] >= 5
    assert result["iterations"] == result["catalog_data_count"]
    assert result["backtest_start"] < result["backtest_end"]
    assert result["run_finished"] is True
    assert result["metrics_present"] is True
    assert "stats_pnls" in result["metric_sections"]
    assert "stats_returns" in result["metric_sections"]
    assert result["orders"] == 0
    assert result["positions"] == 0
    assert result["live_trading_enabled"] is False
    assert result["execution_authority"] is False
    assert result["credentials_used"] is False
