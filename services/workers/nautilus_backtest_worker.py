from __future__ import annotations

from packages.backtest_runner.runner import run_backtest_fixture


def run_worker_fixture() -> dict[str, object]:
    result = run_backtest_fixture(
        strategy_spec_version="0.1.0-draft.1",
        adapter_id="BINANCE_PERP",
        instrument_id="BTCUSDT-PERP",
        compile_hash="fixture",
        worker_image="nautilus-builder-worker:dev",
    )
    return result.model_dump(mode="json")
