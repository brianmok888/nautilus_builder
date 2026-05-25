from __future__ import annotations

from .engine_contract import NAUTILUS_TRADER_VERSION
from .runtime_check import assert_nautilus_runtime_version

REAL_NAUTILUS_ENGINE_SMOKE_MODE = "real_nautilus_engine_smoke"


def run_real_nautilus_backtest_smoke() -> dict[str, object]:
    """Run a minimal real NautilusTrader BacktestEngine lifecycle smoke.

    This proves the pinned NautilusTrader package can initialize, run, and dispose
    the backtest engine in the active environment. It intentionally uses no live
    credentials, no venue adapters, no data, and no strategies; fixture and
    injected-engine evidence remain separate modes for Builder result contracts.
    """

    status = assert_nautilus_runtime_version()

    from nautilus_trader.backtest.engine import BacktestEngine
    from nautilus_trader.config import BacktestEngineConfig, LoggingConfig

    engine = BacktestEngine(
        BacktestEngineConfig(
            logging=LoggingConfig(log_level="ERROR", log_colors=False, print_config=False),
        )
    )
    try:
        engine.run()
        return {
            "engine_mode": REAL_NAUTILUS_ENGINE_SMOKE_MODE,
            "nautilus_trader_version": status.installed_version or NAUTILUS_TRADER_VERSION,
            "run_finished": engine.run_finished is not None,
            "iterations": int(engine.iteration),
            "orders": 0,
            "live_trading_enabled": False,
            "execution_authority": False,
            "credentials_used": False,
        }
    finally:
        engine.dispose()
