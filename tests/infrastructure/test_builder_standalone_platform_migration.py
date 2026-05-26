from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MIGRATION = ROOT / "infra" / "migrations" / "002_builder_standalone_platform.sql"


def _sql() -> str:
    return MIGRATION.read_text()


def _table_block(sql: str, table: str) -> str:
    pattern = rf"CREATE TABLE IF NOT EXISTS builder\.{re.escape(table)}\s*\((.*?)\n\);"
    match = re.search(pattern, sql, re.IGNORECASE | re.DOTALL)
    assert match, f"builder.{table} table is missing"
    return match.group(1)


def _assert_columns(block: str, *columns: str) -> None:
    lowered = block.lower()
    for column in columns:
        assert re.search(rf"\b{re.escape(column.lower())}\b", lowered), f"missing column {column}"


def test_standalone_platform_migration_is_builder_owned_inventory() -> None:
    sql = _sql()

    assert "CREATE SCHEMA IF NOT EXISTS builder" in sql
    assert "Nautilus-Daedalus" not in sql
    assert "DAEDALUS" not in sql
    for forbidden_schema in ("config", "audit", "ai_lane", "promotion", "telegram", "runtime_support"):
        assert f"CREATE SCHEMA IF NOT EXISTS {forbidden_schema}" not in sql

    required_tables = {
        "schema_migrations",
        "runtime_profiles",
        "strategy_specs",
        "strategy_param_versions",
        "active_strategy_params",
        "dataset_manifests",
        "backtest_jobs",
        "backtest_run_manifests",
        "backtest_artifacts",
        "research_jobs",
        "optimizer_trials",
        "ai_threads",
        "ai_draft_audits",
        "ai_result_reviews",
        "ai_improvement_suggestions",
        "ai_experiment_cycles",
        "ai_candidate_rankings",
        "ai_feedback_memory",
        "promotion_candidate_packages",
        "promotion_approvals",
        "paper_runs",
        "live_runs",
        "trade_actions",
        "execution_reports",
        "telegram_users",
        "telegram_subscriptions",
        "telegram_delivery_log",
    }
    for table in sorted(required_tables):
        _table_block(sql, table)


def test_runtime_profiles_are_mode_gated_and_live_disabled_by_default() -> None:
    block = _table_block(_sql(), "runtime_profiles")

    _assert_columns(
        block,
        "runtime_profile_id",
        "tenant_id",
        "project_id",
        "runtime_mode",
        "environment",
        "enabled",
        "advisory_only",
        "manual_review_required",
        "paper_trading_enabled",
        "live_trading_enabled",
        "execution_authority",
        "may_submit_order",
        "risk_profile_id",
        "reconciliation_required",
        "credential_slot_ref",
        "activated_by",
        "activated_at",
        "config_checksum",
        "nautilus_trader_version",
    )
    assert "live_trading_enabled BOOLEAN NOT NULL DEFAULT FALSE" in block
    assert "execution_authority BOOLEAN NOT NULL DEFAULT FALSE" in block
    assert "may_submit_order BOOLEAN NOT NULL DEFAULT FALSE" in block
    assert "paper_trading_enabled BOOLEAN NOT NULL DEFAULT FALSE" in block
    assert "runtime_mode IN ('authoring', 'backtest', 'research', 'optimizer', 'paper', 'live')" in block
    assert "live_authority_requires_activation" in block
    assert "manual_review_required IS TRUE" in block
    assert "reconciliation_required IS TRUE" in block
    assert "risk_profile_id IS NOT NULL" in block
    assert "activated_by IS NOT NULL" in block
    assert "activated_at IS NOT NULL" in block
    assert "NULLIF(config_checksum, '') IS NOT NULL" in block


def test_strategy_data_backtest_and_artifacts_keep_nautilus_lineage() -> None:
    sql = _sql()

    strategy = _table_block(sql, "strategy_specs")
    _assert_columns(
        strategy,
        "strategy_lineage_id",
        "strategy_version_id",
        "parent_strategy_version_id",
        "compile_hash",
        "strategy_class_path",
        "config_class_path",
        "validation_output_mode",
        "strategy_spec",
    )

    dataset = _table_block(sql, "dataset_manifests")
    _assert_columns(
        dataset,
        "dataset_manifest_id",
        "catalog_root_id",
        "catalog_path",
        "source_mode",
        "cache_mode",
        "instrument_id",
        "venue",
        "data_type",
        "data_cls",
        "bar_type",
        "start_ts",
        "end_ts",
        "manifest_checksum",
    )
    assert "catalog_path !~ '(^|/)\\.\\.(/|$)'" in dataset
    assert "source_mode IN ('catalog', 'local_fixture', 'external_mirror_manifest', 'user_fetched_manifest', 'synthetic_test_kit')" in dataset

    backtest = _table_block(sql, "backtest_run_manifests")
    _assert_columns(
        backtest,
        "backtest_job_id",
        "strategy_lineage_id",
        "strategy_version_id",
        "compile_hash",
        "dataset_manifest_id",
        "engine_mode",
        "nautilus_trader_version",
        "artifact_manifest_uri",
        "manifest_checksum",
    )

    artifact = _table_block(sql, "backtest_artifacts")
    _assert_columns(artifact, "artifact_scope", "artifact_uri", "media_type", "checksum", "checksum_algorithm")
    assert "artifact_scope IN ('project_artifact', 'fixture_dev_only', 'external_mirror_manifest', 'user_fetched_manifest')" in artifact
    assert "artifact_uri !~ '(^|/)\\.\\.(/|$)'" in artifact
    assert "artifact_uri LIKE 'artifact://builder/%'" in artifact
    assert "artifact_uri LIKE 'fixture://%'" in artifact
    assert "NULLIF(checksum, '') IS NOT NULL" in artifact
    assert "NULLIF(media_type, '') IS NOT NULL" in artifact


def test_ai_research_promotion_and_runtime_tables_bind_continuous_improvement_chain() -> None:
    sql = _sql()

    for table in ("ai_draft_audits", "ai_result_reviews", "ai_improvement_suggestions", "ai_experiment_cycles", "ai_candidate_rankings"):
        block = _table_block(sql, table)
        _assert_columns(
            block,
            "strategy_lineage_id",
            "strategy_version_id",
            "ai_thread_id",
            "improvement_cycle_id",
        )
        assert "may_submit_order BOOLEAN NOT NULL DEFAULT FALSE" in block or table == "ai_experiment_cycles"

    research = _table_block(sql, "research_jobs")
    _assert_columns(research, "research_job_id", "strategy_lineage_id", "strategy_version_id", "dataset_manifest_id", "manual_promotion_required", "may_submit_order", "execution_authority")
    assert "manual_promotion_required BOOLEAN NOT NULL DEFAULT TRUE" in research
    assert "may_submit_order BOOLEAN NOT NULL DEFAULT FALSE" in research
    assert "execution_authority BOOLEAN NOT NULL DEFAULT FALSE" in research

    trial = _table_block(sql, "optimizer_trials")
    _assert_columns(trial, "optimizer_trial_id", "research_job_id", "strategy_lineage_id", "strategy_version_id", "backtest_run_manifest_id", "candidate_rank")

    package = _table_block(sql, "promotion_candidate_packages")
    _assert_columns(package, "promotion_candidate_id", "strategy_lineage_id", "strategy_version_id", "backtest_run_manifest_id", "optimizer_trial_id", "compile_hash", "manual_review_required")
    assert "manual_review_required BOOLEAN NOT NULL DEFAULT TRUE" in package


def test_paper_live_execution_and_telegram_records_have_safe_authority_shape() -> None:
    sql = _sql()

    paper = _table_block(sql, "paper_runs")
    _assert_columns(paper, "paper_run_id", "runtime_profile_id", "strategy_lineage_id", "strategy_version_id", "simulated_execution", "live_trading_enabled", "may_submit_order")
    assert "simulated_execution BOOLEAN NOT NULL DEFAULT TRUE" in paper
    assert "live_trading_enabled BOOLEAN NOT NULL DEFAULT FALSE" in paper
    assert "may_submit_order BOOLEAN NOT NULL DEFAULT FALSE" in paper

    live = _table_block(sql, "live_runs")
    _assert_columns(live, "live_run_id", "runtime_profile_id", "strategy_lineage_id", "strategy_version_id", "risk_profile_id", "reconciliation_required", "credential_slot_ref", "live_trading_enabled", "execution_authority", "may_submit_order")
    assert "live_run_requires_profile_authority" in live
    assert "live_trading_enabled BOOLEAN NOT NULL DEFAULT FALSE" in live
    assert "execution_authority BOOLEAN NOT NULL DEFAULT FALSE" in live
    assert "may_submit_order BOOLEAN NOT NULL DEFAULT FALSE" in live

    trade_action = _table_block(sql, "trade_actions")
    _assert_columns(
        trade_action,
        "trade_action_id",
        "runtime_profile_id",
        "live_run_id",
        "promotion_approval_id",
        "risk_profile_id",
        "reconciliation_required",
        "strategy_lineage_id",
        "strategy_version_id",
        "order_intent",
        "risk_decision",
        "live_trading_enabled",
        "execution_authority",
        "may_submit_order",
    )
    assert "may_submit_order BOOLEAN NOT NULL DEFAULT FALSE" in trade_action
    assert "trade_action_submit_requires_live_authority" in trade_action
    assert "promotion_approval_id IS NOT NULL" in trade_action
    assert "risk_profile_id IS NOT NULL" in trade_action

    execution = _table_block(sql, "execution_reports")
    _assert_columns(execution, "execution_report_id", "runtime_profile_id", "trade_action_id", "order_id", "venue", "instrument_id", "report_type", "payload")

    for table in ("telegram_users", "telegram_subscriptions", "telegram_delivery_log"):
        block = _table_block(sql, table)
        _assert_columns(block, "tenant_id", "project_id")
    assert "telegram_users_telegram_chat_id_key" in sql
    assert "telegram_delivery_log" in sql and "notification_only" in _table_block(sql, "telegram_delivery_log")


def test_runtime_events_are_enriched_without_replacing_existing_event_log() -> None:
    sql = _sql()

    assert "ALTER TABLE builder.runtime_events" in sql
    for column in (
        "tenant_id",
        "project_id",
        "runtime_profile_id",
        "event_type",
        "stream_name",
        "source_component",
        "strategy_lineage_id",
        "strategy_version_id",
    ):
        assert f"ADD COLUMN IF NOT EXISTS {column}" in sql
