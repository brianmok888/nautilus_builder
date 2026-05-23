from __future__ import annotations

from .artifacts import BacktestResultArtifact


def _list_value(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def normalize_backtest_result(
    *,
    raw_result: dict[str, object],
    strategy_spec_version: str,
    compile_hash: str,
    worker_image: str,
    backtest_job_id: str | None = None,
) -> BacktestResultArtifact:
    trades = _list_value(raw_result.get("trades", []))
    fills = _list_value(raw_result.get("fills", []))
    logs = _list_value(raw_result.get("logs", []))

    return BacktestResultArtifact(
        backtest_job_id=backtest_job_id,
        strategy_spec_version=strategy_spec_version,
        compile_hash=compile_hash,
        worker_image=worker_image,
        summary_metrics={
            "trade_count": len(trades),
            "fill_count": len(fills),
        },
        artifact_refs={
            "result": f"artifact://backtests/{backtest_job_id}/result.json" if backtest_job_id else "result.json",
            "equity_curve": "equity_curve.parquet",
            "trades": "trades.parquet",
            "fills": "fills.parquet",
        },
        logs=[str(entry) for entry in logs],
    )
