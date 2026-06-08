from __future__ import annotations

from typing import Any

from packages.backtest_jobs.models import BacktestJob
from packages.backtest_jobs.postgres_service import PostgresBacktestJobService


def _make_job(
    job_id: str = "bt_scoped",
    strategy_spec_version_id: str = "strategy_001_v001",
) -> BacktestJob:
    return BacktestJob(
        job_id=job_id,
        status="SUCCEEDED",
        stage="SUCCEEDED",
        created_by="builder_api",
        created_at="2026-06-08T00:00:00Z",
        updated_at="2026-06-08T00:00:01Z",
        strategy_spec_version_id=strategy_spec_version_id,
        adapter_profile_id="BINANCE_PERP",
        instrument_id="BTCUSDT-PERP",
        data_range="2025-01-01:2025-06-01",
        worker_id="worker_001",
        result_artifact_refs={"report": "report.json"},
        event_stream_id=f"builder:runtime:{job_id}",
        user_id="u1",
        project_id="p1",
        dataset_id="ds_001",
        catalog_path=None,
        data_type="bars",
        timeframe="5m",
        market_type="crypto_perp",
        compile_hash="a" * 64,
        validation_report_id="vr_001",
        compile_artifact_id="compile_001",
        cancel_requested=False,
    )


class DelegatingRepo:
    def __init__(self, jobs: list[BacktestJob]) -> None:
        self.jobs = jobs
        self.listed_strategy_version_ids: list[str] = []

    def list_by_strategy_version(self, strategy_spec_version_id: str, *, context: Any = None) -> list[BacktestJob]:
        assert context is None
        self.listed_strategy_version_ids.append(strategy_spec_version_id)
        return list(self.jobs)

    def list_all(self) -> list[BacktestJob]:
        raise AssertionError("list_all should not be called for strategy-scoped reads")

    def __getattr__(self, name: str) -> Any:
        raise AssertionError(f"unexpected repo method called: {name}")


def test_postgres_backtest_service_lists_jobs_with_repository_strategy_query() -> None:
    job = _make_job()
    repo = DelegatingRepo([job])
    service = PostgresBacktestJobService(repo)  # type: ignore[arg-type]

    result = service.list_jobs_for_strategy("strategy_001_v001")

    assert result == [job]
    assert repo.listed_strategy_version_ids == ["strategy_001_v001"]
