CREATE SCHEMA IF NOT EXISTS builder;

CREATE TABLE IF NOT EXISTS builder.strategy_identities (
    strategy_id TEXT PRIMARY KEY,
    strategy_lineage_id TEXT NOT NULL,
    payload JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS builder.strategy_versions (
    strategy_version_id TEXT PRIMARY KEY,
    strategy_id TEXT NOT NULL,
    strategy_lineage_id TEXT NOT NULL,
    payload JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS builder.test_jobs (
    test_job_id TEXT PRIMARY KEY,
    strategy_version_id TEXT NOT NULL,
    strategy_lineage_id TEXT NOT NULL,
    payload JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS builder.test_results (
    result_id TEXT PRIMARY KEY,
    test_job_id TEXT NOT NULL,
    strategy_lineage_id TEXT NOT NULL,
    payload JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS builder.ai_suggestions (
    suggestion_id TEXT PRIMARY KEY,
    result_id TEXT NOT NULL,
    strategy_lineage_id TEXT NOT NULL,
    ai_thread_id TEXT NOT NULL,
    payload JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS builder.runtime_events (
    event_sequence BIGSERIAL PRIMARY KEY,
    job_id TEXT NOT NULL,
    payload JSONB NOT NULL
);
