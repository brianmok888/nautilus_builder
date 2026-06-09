"""Versioned Postgres schema migrations for Nautilus Builder.

Each migration has an `up` and optional `down` SQL statement.
`apply_migrations` runs only pending migrations in order.
`rollback` rolls back the last applied migration.
"""
from __future__ import annotations

from typing import Any, NamedTuple

from packages.postgres.identifiers import safe_postgres_identifier


class Migration(NamedTuple):
    version: int
    name: str
    up: str
    down: str


MIGRATIONS: list[Migration] = [
    Migration(
        version=1,
        name="initial_schema",
        up="""
        CREATE TABLE IF NOT EXISTS {schema}.strategies (
            strategy_id       TEXT PRIMARY KEY,
            strategy_lineage_id TEXT NOT NULL,
            status            TEXT NOT NULL DEFAULT 'draft',
            latest_spec       JSONB NOT NULL DEFAULT '{{}}',
            user_id           TEXT NOT NULL DEFAULT 'system',
            project_id        TEXT NOT NULL DEFAULT 'default',
            created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE TABLE IF NOT EXISTS {schema}.strategy_versions (
            strategy_version_id TEXT PRIMARY KEY,
            strategy_id         TEXT NOT NULL REFERENCES {schema}.strategies(strategy_id) ON DELETE CASCADE,
            strategy_lineage_id TEXT NOT NULL,
            spec                JSONB NOT NULL,
            user_id             TEXT NOT NULL DEFAULT 'system',
            project_id          TEXT NOT NULL DEFAULT 'default',
            created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE TABLE IF NOT EXISTS {schema}.adapters (
            adapter_id  TEXT PRIMARY KEY,
            enabled     BOOLEAN NOT NULL DEFAULT true,
            venue       TEXT NOT NULL,
            asset_class TEXT NOT NULL,
            data_modes  JSONB NOT NULL DEFAULT '[]',
            execution_modes JSONB NOT NULL DEFAULT '{{}}'
        );

        CREATE TABLE IF NOT EXISTS {schema}.instruments (
            adapter_id          TEXT NOT NULL REFERENCES {schema}.adapters(adapter_id) ON DELETE CASCADE,
            instrument_id       TEXT NOT NULL,
            market_type         TEXT NOT NULL,
            supported_data_types JSONB NOT NULL DEFAULT '[]',
            supported_timeframes JSONB NOT NULL DEFAULT '[]',
            available_date_ranges JSONB NOT NULL DEFAULT '[]',
            PRIMARY KEY (adapter_id, instrument_id)
        );

        CREATE TABLE IF NOT EXISTS {schema}.schema_migrations (
            version     INT PRIMARY KEY,
            name        TEXT NOT NULL,
            applied_at  TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        """,
        down="""
        DELETE FROM {schema}.schema_migrations WHERE version = 1;
        DROP TABLE IF EXISTS {schema}.schema_migrations;
        DROP TABLE IF EXISTS {schema}.instruments;
        DROP TABLE IF EXISTS {schema}.adapters;
        DROP TABLE IF EXISTS {schema}.strategy_versions;
        DROP TABLE IF EXISTS {schema}.strategies;
        """,
    ),
]


def ensure_schema(conn: Any, schema: str = "builder") -> None:
    """Create the builder schema and schema_migrations table if they don't exist."""
    schema = safe_postgres_identifier(schema)
    conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
    conn.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {schema}.schema_migrations (
            version     INT PRIMARY KEY,
            name        TEXT NOT NULL,
            applied_at  TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )


def current_version(conn: Any, schema: str = "builder") -> int:
    """Return the highest applied migration version, or 0 if none."""
    schema = safe_postgres_identifier(schema)
    ensure_schema(conn, schema)
    row = conn.execute(
        f"SELECT MAX(version) FROM {schema}.schema_migrations"
    ).fetchone()
    return row[0] if row and row[0] is not None else 0


def apply_migrations(conn: Any, schema: str = "builder") -> list[str]:
    """Run all pending migrations. Returns list of applied migration names."""
    schema = safe_postgres_identifier(schema)
    ensure_schema(conn, schema)
    applied: list[str] = []
    version = current_version(conn, schema)
    for migration in MIGRATIONS:
        if migration.version > version:
            conn.execute(migration.up.format(schema=schema))
            conn.execute(
                f"INSERT INTO {schema}.schema_migrations (version, name) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                (migration.version, migration.name),
            )
            applied.append(f"v{migration.version}: {migration.name}")
    return applied


def rollback(conn: Any, schema: str = "builder", steps: int = 1) -> list[str]:
    """Roll back the last N migrations. Returns list of rolled-back names."""
    schema = safe_postgres_identifier(schema)
    ensure_schema(conn, schema)
    rolled_back: list[str] = []
    version = current_version(conn, schema)
    for migration in reversed(MIGRATIONS):
        if len(rolled_back) >= steps:
            break
        if migration.version <= version and migration.down:
            conn.execute(migration.down.format(schema=schema))
            rolled_back.append(f"v{migration.version}: {migration.name}")
    return rolled_back

MIGRATIONS.append(
    Migration(
        version=2,
        name="promotion_ledger_and_audit",
        up="""
        CREATE TABLE IF NOT EXISTS {schema}.compiler_runs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            strategy_id TEXT NOT NULL,
            spec_version_id TEXT NOT NULL,
            compiler_version TEXT NOT NULL,
            compiler_hash TEXT NOT NULL,
            policy_hash TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            output_artifact_hash TEXT,
            output_artifact_uri TEXT,
            error_code TEXT,
            error_message TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            completed_at TIMESTAMPTZ
        );

        CREATE TABLE IF NOT EXISTS {schema}.replay_runs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            strategy_id TEXT NOT NULL,
            compiler_run_id UUID NOT NULL REFERENCES {schema}.compiler_runs(id),
            dataset_hash TEXT NOT NULL,
            dataset_uri TEXT NOT NULL,
            replay_policy_hash TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            report_hash TEXT,
            report_uri TEXT,
            deterministic_output_hash TEXT,
            error_code TEXT,
            error_message TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            completed_at TIMESTAMPTZ
        );

        CREATE TABLE IF NOT EXISTS {schema}.promotion_ledger (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            strategy_id TEXT NOT NULL,
            spec_version_id TEXT NOT NULL,
            compiler_run_id UUID NOT NULL REFERENCES {schema}.compiler_runs(id),
            replay_run_id UUID NOT NULL REFERENCES {schema}.replay_runs(id),
            promotion_mode TEXT NOT NULL,
            strategy_spec_hash TEXT NOT NULL,
            compiler_hash TEXT NOT NULL,
            policy_hash TEXT NOT NULL,
            dataset_hash TEXT NOT NULL,
            replay_report_hash TEXT NOT NULL,
            artifact_hash TEXT NOT NULL,
            artifact_uri TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            requested_by TEXT NOT NULL,
            approved_by TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            approved_at TIMESTAMPTZ
        );

        CREATE TABLE IF NOT EXISTS {schema}.audit_events (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            request_id TEXT NOT NULL,
            actor_id TEXT NOT NULL,
            action TEXT NOT NULL,
            resource_type TEXT NOT NULL,
            resource_id TEXT,
            before_hash TEXT,
            after_hash TEXT,
            status TEXT NOT NULL,
            error_code TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        ALTER TABLE {schema}.schema_migrations ADD COLUMN IF NOT EXISTS checksum TEXT;
        """,
        down="""
        DROP TABLE IF EXISTS {schema}.audit_events;
        DROP TABLE IF EXISTS {schema}.promotion_ledger;
        DROP TABLE IF EXISTS {schema}.replay_runs;
        DROP TABLE IF EXISTS {schema}.compiler_runs;
        ALTER TABLE {schema}.schema_migrations DROP COLUMN IF EXISTS checksum;
        """,
    ),
)



MIGRATIONS.append(
    Migration(
        version=3,
        name="audit_events_project_id",
        up="""
        ALTER TABLE {schema}.audit_events ADD COLUMN IF NOT EXISTS project_id TEXT;
        CREATE INDEX IF NOT EXISTS idx_audit_events_project_id ON {schema}.audit_events (project_id);
        CREATE INDEX IF NOT EXISTS idx_audit_events_actor_id ON {schema}.audit_events (actor_id);
        CREATE INDEX IF NOT EXISTS idx_audit_events_created_at ON {schema}.audit_events (created_at);
        """,
        down="""
        DROP INDEX IF EXISTS {schema}.idx_audit_events_created_at;
        DROP INDEX IF EXISTS {schema}.idx_audit_events_actor_id;
        DROP INDEX IF EXISTS {schema}.idx_audit_events_project_id;
        ALTER TABLE {schema}.audit_events DROP COLUMN IF EXISTS project_id;
        """,
    ),
)


MIGRATIONS.append(
    Migration(
        version=4,
        name="builder_backtest_and_config_tables",
        up="""
        CREATE TABLE IF NOT EXISTS {schema}.backtest_jobs (
            job_id TEXT PRIMARY KEY,
            strategy_id TEXT NOT NULL,
            strategy_spec_version_id TEXT NOT NULL,
            adapter_profile_id TEXT NOT NULL DEFAULT '',
            instrument_id TEXT NOT NULL DEFAULT '',
            data_range TEXT NOT NULL DEFAULT 'unspecified',
            compile_hash TEXT NOT NULL DEFAULT '',
            compile_artifact_id TEXT,
            validation_report_id TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'CREATED',
            stage TEXT NOT NULL DEFAULT 'CREATED',
            lifecycle_status TEXT NOT NULL DEFAULT 'CREATED',
            worker_id TEXT NOT NULL DEFAULT 'unassigned',
            result_artifact_refs JSONB NOT NULL DEFAULT '{{}}',
            event_stream_id TEXT NOT NULL DEFAULT '',
            created_by TEXT NOT NULL DEFAULT 'builder_api',
            user_id TEXT NOT NULL DEFAULT 'system',
            project_id TEXT NOT NULL DEFAULT 'default',
            dataset_id TEXT NOT NULL DEFAULT 'unspecified',
            catalog_path TEXT,
            data_type TEXT NOT NULL DEFAULT 'unspecified',
            timeframe TEXT NOT NULL DEFAULT 'unspecified',
            market_type TEXT NOT NULL DEFAULT 'unspecified',
            cancel_requested BOOLEAN NOT NULL DEFAULT false,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE INDEX IF NOT EXISTS idx_backtest_jobs_strategy_id ON {schema}.backtest_jobs (strategy_id);
        CREATE INDEX IF NOT EXISTS idx_backtest_jobs_strategy_spec_version_id ON {schema}.backtest_jobs (strategy_spec_version_id);
        CREATE INDEX IF NOT EXISTS idx_backtest_jobs_status ON {schema}.backtest_jobs (status);
        CREATE INDEX IF NOT EXISTS idx_backtest_jobs_created_at ON {schema}.backtest_jobs (created_at);

        CREATE TABLE IF NOT EXISTS {schema}.backtest_results (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            job_id TEXT NOT NULL REFERENCES {schema}.backtest_jobs(job_id) ON DELETE CASCADE,
            strategy_id TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'unknown',
            summary JSONB NOT NULL DEFAULT '{{}}',
            metrics JSONB NOT NULL DEFAULT '{{}}',
            result_artifact_refs JSONB NOT NULL DEFAULT '{{}}',
            report_artifact_id TEXT,
            report_artifact_ref TEXT,
            report_hash TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE INDEX IF NOT EXISTS idx_backtest_results_job_id ON {schema}.backtest_results (job_id);
        CREATE INDEX IF NOT EXISTS idx_backtest_results_strategy_id ON {schema}.backtest_results (strategy_id);

        CREATE TABLE IF NOT EXISTS {schema}.builder_config (
            key TEXT PRIMARY KEY,
            value JSONB NOT NULL DEFAULT '{{}}',
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_by TEXT
        );

        CREATE TABLE IF NOT EXISTS {schema}.workflow_results (
            result_id TEXT PRIMARY KEY,
            test_job_id TEXT NOT NULL,
            strategy_lineage_id TEXT NOT NULL DEFAULT '',
            project_id TEXT NOT NULL DEFAULT 'default',
            payload JSONB NOT NULL DEFAULT '{{}}',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE INDEX IF NOT EXISTS idx_workflow_results_test_job_id ON {schema}.workflow_results (test_job_id);
        CREATE INDEX IF NOT EXISTS idx_workflow_results_strategy_lineage_id ON {schema}.workflow_results (strategy_lineage_id);
        """,
        down="""
        DROP INDEX IF EXISTS {schema}.idx_workflow_results_strategy_lineage_id;
        DROP INDEX IF EXISTS {schema}.idx_workflow_results_test_job_id;
        DROP TABLE IF EXISTS {schema}.workflow_results;
        DROP TABLE IF EXISTS {schema}.builder_config;
        DROP INDEX IF EXISTS {schema}.idx_backtest_results_strategy_id;
        DROP INDEX IF EXISTS {schema}.idx_backtest_results_job_id;
        DROP TABLE IF EXISTS {schema}.backtest_results;
        DROP INDEX IF EXISTS {schema}.idx_backtest_jobs_created_at;
        DROP INDEX IF EXISTS {schema}.idx_backtest_jobs_status;
        DROP INDEX IF EXISTS {schema}.idx_backtest_jobs_strategy_spec_version_id;
        DROP INDEX IF EXISTS {schema}.idx_backtest_jobs_strategy_id;
        DROP TABLE IF EXISTS {schema}.backtest_jobs;
        """,
    ),
)


MIGRATIONS.append(
    Migration(
        version=5,
        name="strategy_scope_columns",
        up="""
        ALTER TABLE {schema}.strategies
            ADD COLUMN IF NOT EXISTS user_id TEXT NOT NULL DEFAULT 'system',
            ADD COLUMN IF NOT EXISTS project_id TEXT NOT NULL DEFAULT 'default';

        ALTER TABLE {schema}.strategy_versions
            ADD COLUMN IF NOT EXISTS user_id TEXT NOT NULL DEFAULT 'system',
            ADD COLUMN IF NOT EXISTS project_id TEXT NOT NULL DEFAULT 'default';

        CREATE INDEX IF NOT EXISTS idx_strategies_scope
            ON {schema}.strategies(user_id, project_id);

        CREATE INDEX IF NOT EXISTS idx_strategy_versions_scope
            ON {schema}.strategy_versions(user_id, project_id);
        """,
        down="""
        DROP INDEX IF EXISTS {schema}.idx_strategy_versions_scope;
        DROP INDEX IF EXISTS {schema}.idx_strategies_scope;
        ALTER TABLE {schema}.strategy_versions
            DROP COLUMN IF EXISTS project_id,
            DROP COLUMN IF EXISTS user_id;
        ALTER TABLE {schema}.strategies
            DROP COLUMN IF EXISTS project_id,
            DROP COLUMN IF EXISTS user_id;
        """,
    )
)


MIGRATIONS.append(
    Migration(
        version=6,
        name="audit_events_project_id_not_null",
        up="""
        ALTER TABLE {schema}.audit_events ADD COLUMN IF NOT EXISTS project_id TEXT NOT NULL DEFAULT 'unknown';
        UPDATE {schema}.audit_events SET project_id = 'unknown' WHERE project_id IS NULL;
        ALTER TABLE {schema}.audit_events ALTER COLUMN project_id SET DEFAULT 'unknown';
        ALTER TABLE {schema}.audit_events ALTER COLUMN project_id SET NOT NULL;
        CREATE INDEX IF NOT EXISTS idx_audit_events_project_id ON {schema}.audit_events (project_id);
        """,
        down="""
        ALTER TABLE {schema}.audit_events ALTER COLUMN project_id DROP NOT NULL;
        ALTER TABLE {schema}.audit_events ALTER COLUMN project_id DROP DEFAULT;
        """,
    )
)
