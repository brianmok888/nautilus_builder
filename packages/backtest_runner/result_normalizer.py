from __future__ import annotations

from .artifacts import BacktestResultArtifact


def normalize_backtest_result(
    *,
    raw_result: dict[str, object],
    strategy_spec_version: str,
    compile_hash: str,
    worker_image: str,
) -> BacktestResultArtifact:
    trades = list(raw_result.get("trades", []))
    fills = list(raw_result.get("fills", []))
    logs = list(raw_result.get("logs", []))

    return BacktestResultArtifact(
        strategy_spec_version=strategy_spec_version,
        compile_hash=compile_hash,
        worker_image=worker_image,
        summary_metrics={
            "trade_count": len(trades),
            "fill_count": len(fills),
        },
        artifact_refs={
            "equity_curve": "equity_curve.parquet",
            "trades": "trades.parquet",
            "fills": "fills.parquet",
        },
        logs=[str(entry) for entry in logs],
    )
