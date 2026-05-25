from __future__ import annotations

from packages.backtest_runner.runner import run_backtest_fixture


def test_worker_runs_minimal_fixture_backtest() -> None:
    result = run_backtest_fixture(
        strategy_spec_version="0.1.0-draft.1",
        adapter_id="BINANCE_PERP",
        instrument_id="BTCUSDT-PERP",
        compile_hash="abc123",
        worker_image="nautilus-builder-worker:dev",
    )

    assert result.strategy_spec_version == "0.1.0-draft.1"
    assert result.compile_hash == "abc123"
    assert result.worker_image == "nautilus-builder-worker:dev"
    assert result.summary_metrics["trade_count"] >= 0
    assert len(result.logs) >= 1


def test_worker_result_preserves_backend_job_identity() -> None:
    result = run_backtest_fixture(
        backtest_job_id="job_001",
        strategy_spec_version="0.1.0-draft.1",
        adapter_id="BINANCE_PERP",
        instrument_id="BTCUSDT-PERP",
        compile_hash="abc123",
        worker_image="nautilus-builder-worker:dev",
    )

    assert result.backtest_job_id == "job_001"
    assert result.artifact_refs["result"] == "fixture://backtests/job_001/result.json"
    assert result.artifact_refs["fixture_evidence_only"] == "true"
