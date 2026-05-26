from __future__ import annotations

import pytest

from packages.research_jobs import ResearchJobService


def _payload() -> dict[str, object]:
    return {
        "strategy_lineage_id": "strat_lineage_001",
        "strategy_version_id": "strategy_001_v002",
        "dataset_id": "ds_btcusdt_perp_2025",
        "job_type": "parameter_search",
        "parameter_grid": {"ema_fast": [8, 12], "ema_slow": [21, 34]},
        "train_windows": [{"name": "train_q1", "date_range": "2025-01-01:2025-02-01"}],
        "holdout_windows": [{"name": "holdout_feb", "date_range": "2025-02-01:2025-03-01"}],
        "max_trials": 4,
        "created_by": "user_123",
        "project_id": "project_alpha",
    }


def test_research_job_service_creates_offline_parameter_search_job() -> None:
    service = ResearchJobService()

    job = service.create_job(_payload())

    assert job.research_job_id.startswith("research_job_")
    assert job.status == "QUEUED"
    assert job.job_type == "parameter_search"
    assert job.strategy_version_id == "strategy_001_v002"
    assert job.dataset_id == "ds_btcusdt_perp_2025"
    assert job.execution_mode == "offline_research"
    assert job.max_trials == 4
    assert job.manual_promotion_required is True
    assert job.may_submit_order is False
    assert job.live_trading_enabled is False
    assert job.execution_authority is False
    assert job.parameter_grid["ema_fast"] == [8, 12]


def test_research_job_rejects_empty_parameter_grid() -> None:
    service = ResearchJobService()
    payload = _payload()
    payload["parameter_grid"] = {}

    with pytest.raises(ValueError, match="parameter_grid must not be empty"):
        service.create_job(payload)


def test_research_job_rejects_live_or_auto_promotion_modes() -> None:
    service = ResearchJobService()
    payload = _payload()
    payload["execution_mode"] = "live"

    with pytest.raises(ValueError, match="offline_research"):
        service.create_job(payload)

    payload = _payload()
    payload["auto_promote"] = True

    with pytest.raises(ValueError, match="manual promotion"):
        service.create_job(payload)
