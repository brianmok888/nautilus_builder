from __future__ import annotations

from .artifacts import BacktestResultArtifact
from .contracts import build_report_summary
from .engine_contract import FIXTURE_ENGINE_MODE, NAUTILUS_TRADER_VERSION


def _list_value(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def normalize_backtest_result(
    *,
    raw_result: dict[str, object],
    strategy_spec_version: str,
    compile_hash: str,
    worker_image: str,
    backtest_job_id: str | None = None,
    engine_mode: str = FIXTURE_ENGINE_MODE,
) -> BacktestResultArtifact:
    trades = _list_value(raw_result.get("trades", []))
    fills = _list_value(raw_result.get("fills", []))
    logs = _list_value(raw_result.get("logs", []))

    fixture_evidence_only = engine_mode == FIXTURE_ENGINE_MODE
    result_ref = (
        f"fixture://backtests/{backtest_job_id}/result.json"
        if fixture_evidence_only and backtest_job_id
        else "fixture://backtests/result.json"
        if fixture_evidence_only
        else f"artifact://backtests/{backtest_job_id}/result.json"
        if backtest_job_id
        else "result.json"
    )

    return BacktestResultArtifact(
        backtest_job_id=backtest_job_id,
        strategy_spec_version=strategy_spec_version,
        compile_hash=compile_hash,
        worker_image=worker_image,
        engine_mode=engine_mode,
        nautilus_trader_version=NAUTILUS_TRADER_VERSION,
        summary_metrics={
            "trade_count": len(trades),
            "fill_count": len(fills),
        },
        artifact_refs={
            "result": result_ref,
            "equity_curve": "equity_curve.parquet",
            "trades": "trades.parquet",
            "fills": "fills.parquet",
            "evidence_mode": engine_mode,
            "fixture_evidence_only": "true" if fixture_evidence_only else "false",
        },
        logs=[str(entry) for entry in logs],
        report_summary=build_report_summary(raw_result),
    )
