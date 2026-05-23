from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_frontend_plan_names_canonical_strategy_spec_as_param_source() -> None:
    plan = (ROOT / "docs" / "superpowers" / "plans" / "2026-05-23-frontend-ready-operator-mvp-implementation-plan.md").read_text()
    strategy_model = (ROOT / "packages" / "strategy_spec" / "models.py").read_text()

    assert "Frontend must never invent strategy params outside `StrategySpec` schema" in plan
    assert "class StrategySpec" in strategy_model


def test_ai_lane_and_nd_alignment_require_stable_backend_ids() -> None:
    plan = (ROOT / "docs" / "superpowers" / "plans" / "2026-05-23-frontend-ready-operator-mvp-implementation-plan.md").read_text()
    nd_test = (ROOT / "tests" / "workflow_spine" / "test_nd_ai_compatibility.py").read_text()

    for required in ("ai_thread_id", "improvement_cycle_id", "strategy_lineage_id", "strategy_version_id"):
        assert required in plan
        assert required in nd_test
    assert "builder:nd:advisory" in nd_test
    assert "nd:ai:pipeline" in nd_test


def test_postgres_and_redis_are_builder_owned_contracts() -> None:
    migration = (ROOT / "infra" / "migrations" / "001_builder_workflow_storage.sql").read_text()
    redis_stream = (ROOT / "packages" / "runtime_events" / "redis_stream.py").read_text()

    assert "CREATE SCHEMA IF NOT EXISTS builder" in migration
    assert "strategy_lineage_id" in migration
    assert "ai_thread_id" in migration
    assert "builder:runtime:{job_id}" in redis_stream
    assert "namespace != \"builder\"" in redis_stream


def test_nt_boundary_requires_validated_backend_owned_config() -> None:
    plan = (ROOT / "docs" / "superpowers" / "plans" / "2026-05-23-frontend-ready-operator-mvp-implementation-plan.md").read_text()
    nt_boundary = (ROOT / "packages" / "backtest_runner" / "nautilus_engine.py").read_text()

    assert "validated StrategySpec version + adapter/instrument profile + compile/validation artifacts" in plan
    assert "build_backtest_config" in nt_boundary
    assert "strategy_spec_version" in nt_boundary
    assert "validation_report_id" in nt_boundary
