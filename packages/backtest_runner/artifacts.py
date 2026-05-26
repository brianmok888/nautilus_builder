from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from .contracts import BacktestReportSummary


class BacktestResultArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    backtest_job_id: str | None = None
    strategy_spec_version: str
    compile_hash: str
    worker_image: str
    engine_mode: str
    nautilus_trader_version: str
    summary_metrics: dict[str, float | int]
    artifact_refs: dict[str, str]
    logs: list[str]
    report_summary: BacktestReportSummary | None = None
