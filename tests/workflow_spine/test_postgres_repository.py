from __future__ import annotations

import sqlite3

from packages.workflow_spine import (
    AiSuggestionRecord,
    SqliteWorkflowRepository,
    PostgresWorkflowRepository,
    StrategyIdentity,
    StrategyTestParams,
    StrategyVersionIdentity,
    WorkflowJobRecord,
    WorkflowResultRecord,
    workflow_schema_statements,
)


def test_workflow_schema_creates_required_tables() -> None:
    connection = sqlite3.connect(":memory:")

    for statement in workflow_schema_statements(schema="builder"):
        connection.execute(statement)

    table_names = {
        row[0]
        for row in connection.execute("select name from sqlite_master where type = 'table'").fetchall()
    }

    assert "builder_strategy_identities" in table_names
    assert "builder_strategy_versions" in table_names
    assert "builder_test_jobs" in table_names
    assert "builder_test_results" in table_names
    assert "builder_ai_suggestions" in table_names


def test_postgres_workflow_repository_persists_records_across_instances() -> None:
    connection = sqlite3.connect(":memory:")
    repository = PostgresWorkflowRepository(connection=connection, schema="builder")
    strategy = StrategyIdentity(strategy_id="strat_001", strategy_lineage_id="lineage_001", display_name="EMA RSI")
    version = StrategyVersionIdentity(
        strategy_id="strat_001",
        strategy_lineage_id="lineage_001",
        strategy_version_id="sv_001",
        ai_thread_id="ai_thread_001",
        improvement_cycle_id="cycle_001",
    )
    job = WorkflowJobRecord(
        test_job_id="job_001",
        project_id="project_001",
        strategy_version_id="sv_001",
        strategy_lineage_id="lineage_001",
        test_type="backtest",
        params=StrategyTestParams(
            test_type="backtest",
            instrument="BTCUSDT-PERP",
            data_source="BINANCE_PERP",
            timeframe="1-MINUTE",
            start="2025-01-01",
            end="2025-01-31",
        ),
    )
    result = WorkflowResultRecord(
        result_id="res_001",
        test_job_id="job_001",
        project_id="project_001",
        strategy_lineage_id="lineage_001",
        strategy_version_id="sv_001",
        metrics={"sharpe": 1.25},
        artifact_refs={"report": "artifact://res_001/report.json"},
    )
    suggestion = AiSuggestionRecord(
        suggestion_id="sug_001",
        project_id="project_001",
        strategy_lineage_id="lineage_001",
        strategy_version_id="sv_001",
        result_id="res_001",
        ai_thread_id="ai_thread_001",
        improvement_cycle_id="cycle_001",
        suggestion_type="parameter_adjustment",
        message="Lower threshold and retest.",
    )

    repository.save_strategy(strategy)
    repository.save_version(version)
    repository.save_job(job)
    repository.save_result(result)
    repository.save_ai_suggestion(suggestion)
    reloaded = PostgresWorkflowRepository(connection=connection, schema="builder")

    assert reloaded.strategy("strat_001") == strategy
    assert reloaded.version("sv_001") == version
    assert reloaded.job("job_001") == job
    assert reloaded.result("res_001") == result
    assert reloaded.suggestions_for_lineage("lineage_001") == [suggestion]


def test_sqlite_workflow_repository_is_the_honest_contract_name() -> None:
    connection = sqlite3.connect(":memory:")
    repository = SqliteWorkflowRepository(connection=connection, schema="builder")

    assert repository.backend == "sqlite"
    assert PostgresWorkflowRepository is SqliteWorkflowRepository
