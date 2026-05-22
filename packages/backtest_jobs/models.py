from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class BacktestJob(BaseModel):
    model_config = ConfigDict(extra="forbid")

    job_id: str
    stage: str
    strategy_spec_version: str
    adapter_id: str
    instrument_id: str
    compile_hash: str
    validation_report_id: str
    cancel_requested: bool = False
