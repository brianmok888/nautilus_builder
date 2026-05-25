from __future__ import annotations

from packages.backtest_runner.engine_contract import FIXTURE_ENGINE_MODE, INJECTED_ENGINE_MODE, NAUTILUS_TRADER_VERSION
from packages.backtest_runner.real_engine_smoke import run_real_nautilus_backtest_smoke


def test_real_nautilus_backtest_smoke_runs_engine_lifecycle_without_live_authority() -> None:
    result = run_real_nautilus_backtest_smoke()

    assert result["engine_mode"] == "real_nautilus_engine_smoke"
    assert result["engine_mode"] not in {FIXTURE_ENGINE_MODE, INJECTED_ENGINE_MODE}
    assert result["nautilus_trader_version"] == NAUTILUS_TRADER_VERSION
    assert result["live_trading_enabled"] is False
    assert result["execution_authority"] is False
    assert result["credentials_used"] is False
    assert result["run_finished"] is True
    assert result["iterations"] == 0
    assert result["orders"] == 0
