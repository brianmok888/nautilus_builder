from __future__ import annotations

import pytest

from packages.backtest_runner.contracts import (
    BacktestArtifactRef,
    BacktestRunRequest,
    build_backtest_run_manifest,
    build_report_summary,
)


def _run_request() -> BacktestRunRequest:
    return BacktestRunRequest(
        user_id="user_123",
        project_id="project_alpha",
        strategy_lineage_id="strat_lineage_001",
        strategy_version_id="strategy_001_v002",
        compile_hash="abc123def456",
        validation_report_id="vr_001",
        dataset_id="ds_btcusdt_perp_2025",
        catalog_path="/catalogs/project_alpha/ds_btcusdt_perp_2025",
        source_mode="catalog",
        dataset_source="user_selected_catalog",
        adapter_id="BINANCE_PERP",
        instrument_id="BTCUSDT-PERP",
        requested_data_type="quote_ticks",
        timeframe="1m",
        market_type="crypto_perp",
        date_range="2025-01-01:2025-03-01",
        engine_mode="strategy_spec_catalog_replay",
    )


def test_backtest_run_manifest_binds_strategy_dataset_engine_and_hardguard_state() -> None:
    request = _run_request()
    artifact = BacktestArtifactRef(
        name="result_json",
        uri="artifact://builder/project_alpha/user_123/BacktestResult/bt_001_result",
        media_type="application/json",
        checksum_sha256="a" * 64,
        scope="project_artifact",
    )

    manifest = build_backtest_run_manifest(
        request=request,
        artifacts=[artifact],
        raw_result={
            "equity_curve": [10000.0, 10080.0, 10040.0],
            "trades": [{"trade_id": "T-1", "pnl": 40.0}],
            "fills": [{"fill_id": "F-1", "price": 61234.5}],
            "orders": 0,
            "positions": 0,
        },
        started_at="2026-05-26T10:00:00Z",
        finished_at="2026-05-26T10:00:03Z",
        worker_id="nautilus-builder-worker:dev",
    )

    assert manifest.run_id.startswith("bt_run_")
    assert manifest.strategy_lineage_id == "strat_lineage_001"
    assert manifest.strategy_version_id == "strategy_001_v002"
    assert manifest.compile_hash == "abc123def456"
    assert manifest.dataset.dataset_id == "ds_btcusdt_perp_2025"
    assert manifest.dataset.catalog_path == "/catalogs/project_alpha/ds_btcusdt_perp_2025"
    assert manifest.dataset.source_mode == "catalog"
    assert manifest.dataset.requested_data_type == "quote_ticks"
    assert manifest.engine_mode == "strategy_spec_catalog_replay"
    assert manifest.started_at == "2026-05-26T10:00:00Z"
    assert manifest.finished_at == "2026-05-26T10:00:03Z"
    assert manifest.worker_id == "nautilus-builder-worker:dev"
    assert manifest.orders == 0
    assert manifest.positions == 0
    assert manifest.credentials_used is False
    assert manifest.live_trading_enabled is False
    assert manifest.execution_authority is False
    assert manifest.artifacts[0].name == "result_json"
    assert manifest.report_summary.metrics["trade_count"] == 1
    assert manifest.report_summary.metrics["fill_count"] == 1
    assert manifest.manifest_checksum_sha256 != ""


def test_backtest_run_id_is_deterministic_for_same_request() -> None:
    request = _run_request()

    assert request.run_id == _run_request().run_id
    assert request.run_id.startswith("bt_run_")


def test_artifact_refs_require_safe_scope_checksum_media_type_and_uri() -> None:
    valid = BacktestArtifactRef(
        name="equity_curve",
        uri="artifact://builder/project_alpha/user_123/BacktestResult/equity_curve",
        media_type="application/vnd.apache.parquet",
        checksum_sha256="b" * 64,
        scope="project_artifact",
    )

    assert valid.scope == "project_artifact"

    with pytest.raises(ValueError, match="checksum_sha256"):
        BacktestArtifactRef(
            name="result_json",
            uri="artifact://builder/project_alpha/user_123/BacktestResult/result",
            media_type="application/json",
            checksum_sha256="missing",
            scope="project_artifact",
        )

    with pytest.raises(ValueError, match="artifact URI must not contain traversal"):
        BacktestArtifactRef(
            name="result_json",
            uri="artifact://builder/project_alpha/user_123/../secret",
            media_type="application/json",
            checksum_sha256="c" * 64,
            scope="project_artifact",
        )

    with pytest.raises(ValueError, match="project artifacts must use artifact://builder"):
        BacktestArtifactRef(
            name="result_json",
            uri="file:///tmp/result.json",
            media_type="application/json",
            checksum_sha256="d" * 64,
            scope="project_artifact",
        )


def test_fixture_artifact_refs_are_explicitly_dev_only() -> None:
    fixture = BacktestArtifactRef(
        name="result_json",
        uri="fixture://backtests/res_001/result.json",
        media_type="application/json",
        checksum_sha256="e" * 64,
        scope="fixture_dev_only",
    )

    assert fixture.scope == "fixture_dev_only"

    with pytest.raises(ValueError, match="fixture artifacts must use fixture://"):
        BacktestArtifactRef(
            name="result_json",
            uri="artifact://builder/project/user/type/id",
            media_type="application/json",
            checksum_sha256="f" * 64,
            scope="fixture_dev_only",
        )


def test_report_summary_derives_equity_metrics_and_sections_without_live_authority() -> None:
    summary = build_report_summary(
        {
            "equity_curve": [100.0, 110.0, 105.0],
            "trades": [{"id": "T-1"}, {"id": "T-2"}],
            "fills": [{"id": "F-1"}],
        }
    )

    assert summary.metrics["trade_count"] == 2
    assert summary.metrics["fill_count"] == 1
    assert summary.metrics["equity_points"] == 3
    assert summary.metrics["total_return"] == pytest.approx(0.05)
    assert summary.metrics["max_drawdown"] == pytest.approx(-0.045454545454545456)
    assert summary.sections == ["summary", "equity_curve", "trades", "fills", "artifacts"]
    assert summary.chart_sections == ["equity_curve", "drawdown"]
    assert summary.live_trading_enabled is False
    assert summary.execution_authority is False
