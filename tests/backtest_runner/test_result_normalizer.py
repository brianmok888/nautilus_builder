from __future__ import annotations

from packages.backtest_runner.result_normalizer import normalize_backtest_result


def test_result_normalizer_includes_expected_artifacts() -> None:
    normalized = normalize_backtest_result(
        backtest_job_id="job_001",
        raw_result={
            "equity_curve": [10000.0, 10120.5],
            "trades": [{"side": "BUY", "pnl": 120.5}],
            "fills": [{"price": 50000.0, "qty": 0.1}],
            "logs": ["started", "finished"],
        },
        strategy_spec_version="0.1.0-draft.1",
        compile_hash="abc123",
        worker_image="nautilus-builder-worker:dev",
    )

    assert normalized.backtest_job_id == "job_001"
    assert normalized.artifact_refs["equity_curve"] == "equity_curve.parquet"
    assert normalized.artifact_refs["trades"] == "trades.parquet"
    assert normalized.artifact_refs["fills"] == "fills.parquet"
    assert normalized.summary_metrics["trade_count"] == 1
    assert normalized.logs == ["started", "finished"]
