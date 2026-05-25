from __future__ import annotations

from packages.backtest_jobs.service import BacktestJobService


def test_backtest_job_records_user_project_and_catalog_dataset_selection() -> None:
    service = BacktestJobService()

    job = service.create_job(
        {
            "strategy_spec_version_id": "strategy_001_v001",
            "adapter_profile_id": "BINANCE_PERP",
            "instrument_id": "BTCUSDT-PERP",
            "compile_hash": "compile_001",
            "validation_report_id": "validation_001",
            "created_by": "operator_001",
            "user_id": "user_123",
            "project_id": "project_alpha",
            "dataset_id": "ds_btcusdt_perp_2024_q1",
            "catalog_path": "/tmp/nb/catalogs/ds_btcusdt_perp_2024_q1",
            "data_range": "2024-01-01:2024-03-01",
        }
    )

    assert job.user_id == "user_123"
    assert job.project_id == "project_alpha"
    assert job.dataset_id == "ds_btcusdt_perp_2024_q1"
    assert job.catalog_path == "/tmp/nb/catalogs/ds_btcusdt_perp_2024_q1"
    assert job.scoped_artifact.artifact_type == "BacktestJob"
