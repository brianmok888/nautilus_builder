from __future__ import annotations

from .config_builder import build_backtest_config
from .result_normalizer import normalize_backtest_result


def run_backtest_fixture(
    *,
    strategy_spec_version: str,
    adapter_id: str,
    instrument_id: str,
    compile_hash: str,
    worker_image: str,
):
    build_backtest_config(
        strategy_spec_version=strategy_spec_version,
        adapter_id=adapter_id,
        instrument_id=instrument_id,
        compile_hash=compile_hash,
        validation_report_id="vr_fixture",
        worker_image=worker_image,
    )

    raw_result = {
        "equity_curve": [10000.0, 10050.0, 10120.5],
        "trades": [{"side": "BUY", "pnl": 120.5}],
        "fills": [{"price": 50000.0, "qty": 0.1}],
        "logs": ["worker started", "worker finished"],
    }
    return normalize_backtest_result(
        raw_result=raw_result,
        strategy_spec_version=strategy_spec_version,
        compile_hash=compile_hash,
        worker_image=worker_image,
    )
