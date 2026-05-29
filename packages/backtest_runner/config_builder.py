from __future__ import annotations

from .engine_contract import FIXTURE_ENGINE_MODE, NAUTILUS_TRADER_VERSION


def build_backtest_config(
    *,
    strategy_spec_version: str,
    adapter_id: str,
    instrument_id: str,
    compile_hash: str,
    validation_report_id: str,
    worker_image: str,
    engine_mode: str = FIXTURE_ENGINE_MODE,
    credentials: dict[str, str] | None = None,
) -> dict[str, object]:
    if credentials:
        raise ValueError("live credentials are not allowed in Builder backtest config")

    return {
        "strategy_spec_version": strategy_spec_version,
        "adapter_id": adapter_id,
        "instrument_id": instrument_id,
        "compile_hash": compile_hash,
        "validation_report_id": validation_report_id,
        "worker_image": worker_image,
        "engine_mode": engine_mode,
        "nautilus_trader_version": NAUTILUS_TRADER_VERSION,
        "live_trading_enabled": False,
        "execution_authority": False,
        "trade_execution": False,
    }
