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


def test_fixture_result_normalizer_labels_unscoped_refs_as_fixture_only() -> None:
    normalized = normalize_backtest_result(
        backtest_job_id="job_001",
        raw_result={"trades": [], "fills": [], "logs": []},
        strategy_spec_version="0.1.0-draft.1",
        compile_hash="abc123",
        worker_image="nautilus-builder-worker:dev",
    )

    assert normalized.artifact_refs["evidence_mode"] == "fixture"
    assert normalized.artifact_refs["fixture_evidence_only"] == "true"
    assert normalized.artifact_refs["result"].startswith("fixture://backtests/")


def test_injected_engine_result_refs_are_not_marked_as_fixture_only() -> None:
    normalized = normalize_backtest_result(
        backtest_job_id="job_001",
        raw_result={"trades": [], "fills": [], "logs": []},
        strategy_spec_version="0.1.0-draft.1",
        compile_hash="abc123",
        worker_image="nautilus-builder-worker:dev",
        engine_mode="injected_engine",
    )

    assert normalized.artifact_refs["evidence_mode"] == "injected_engine"
    assert normalized.artifact_refs["fixture_evidence_only"] == "false"
    assert normalized.artifact_refs["result"] == "artifact://builder/default/system/backtest_result/job_001"


def test_injected_engine_result_refs_use_scoped_builder_artifact_uri() -> None:
    normalized = normalize_backtest_result(
        backtest_job_id="job_001",
        raw_result={"trades": [], "fills": [], "logs": []},
        strategy_spec_version="0.1.0-draft.1",
        compile_hash="a" * 64,
        worker_image="nautilus-builder-worker:dev",
        engine_mode="injected_engine",
        project_id="project_alpha",
        user_id="user_123",
    )

    assert normalized.artifact_refs["result"] == "artifact://builder/project_alpha/user_123/backtest_result/job_001"
