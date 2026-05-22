from __future__ import annotations

from packages.backtest_jobs.service import BacktestJobService


def test_job_creation_is_idempotent() -> None:
    service = BacktestJobService()

    payload = {
        "strategy_spec_version": "0.1.0-draft.1",
        "adapter_id": "BINANCE_PERP",
        "instrument_id": "BTCUSDT-PERP",
        "compile_hash": "abc123",
        "validation_report_id": "vr_001",
    }

    first = service.create_job(payload)
    second = service.create_job(payload)

    assert first.job_id == second.job_id
    assert first.stage == "CREATED"
    assert first.compile_hash == "abc123"
