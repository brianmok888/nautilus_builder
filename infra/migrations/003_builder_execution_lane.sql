CREATE SCHEMA IF NOT EXISTS builder;

CREATE TABLE IF NOT EXISTS builder.execution_lane_runs (
    execution_lane_run_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    runtime_profile_id TEXT NOT NULL,
    lane_mode TEXT NOT NULL,
    worker_id TEXT,
    status TEXT NOT NULL DEFAULT 'CREATED',
    consumes_stream TEXT NOT NULL,
    strategy_lane_coupled BOOLEAN NOT NULL DEFAULT FALSE,
    advisory_only BOOLEAN NOT NULL DEFAULT TRUE,
    manual_review_required BOOLEAN NOT NULL DEFAULT TRUE,
    paper_trading_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    live_trading_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    execution_authority BOOLEAN NOT NULL DEFAULT FALSE,
    may_submit_order BOOLEAN NOT NULL DEFAULT FALSE,
    risk_profile_id TEXT,
    reconciliation_required BOOLEAN NOT NULL DEFAULT TRUE,
    credential_slot_ref TEXT,
    activated_by TEXT,
    activated_at TIMESTAMPTZ,
    config_checksum TEXT,
    nautilus_trader_version TEXT,
    started_at TIMESTAMPTZ,
    stopped_at TIMESTAMPTZ,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT execution_lane_runs_mode_check CHECK (lane_mode IN ('paper', 'live')),
    CONSTRAINT execution_lane_runs_decoupled CHECK (strategy_lane_coupled IS FALSE),
    CONSTRAINT live_authority_requires_activation CHECK (
        (live_trading_enabled IS FALSE AND execution_authority IS FALSE AND may_submit_order IS FALSE)
        OR (
            lane_mode = 'live'
            AND status IN ('CREATED', 'RUNNING')
            AND live_trading_enabled IS TRUE
            AND execution_authority IS TRUE
            AND may_submit_order IS TRUE
            AND advisory_only IS FALSE
            AND manual_review_required IS TRUE
            AND reconciliation_required IS TRUE
            AND risk_profile_id IS NOT NULL
            AND credential_slot_ref IS NOT NULL
            AND activated_by IS NOT NULL
            AND activated_at IS NOT NULL
            AND NULLIF(config_checksum, '') IS NOT NULL
        )
    ),
    CONSTRAINT paper_execution_lane_no_live_authority CHECK (
        lane_mode <> 'paper'
        OR (live_trading_enabled IS FALSE AND execution_authority IS FALSE AND may_submit_order IS FALSE)
    )
);

CREATE TABLE IF NOT EXISTS builder.execution_lane_commands (
    execution_lane_command_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    runtime_profile_id TEXT NOT NULL,
    execution_lane_run_id TEXT,
    lane_mode TEXT NOT NULL,
    trade_action_id TEXT NOT NULL,
    source_event_id TEXT NOT NULL,
    idempotency_key TEXT NOT NULL,
    strategy_lineage_id TEXT NOT NULL,
    strategy_version_id TEXT NOT NULL,
    promotion_approval_id TEXT,
    risk_profile_id TEXT,
    reconciliation_required BOOLEAN NOT NULL DEFAULT TRUE,
    credential_slot_ref TEXT,
    order_intent JSONB NOT NULL,
    risk_decision JSONB NOT NULL DEFAULT '{}'::jsonb,
    status TEXT NOT NULL DEFAULT 'QUEUED',
    claimed_by TEXT,
    claimed_at TIMESTAMPTZ,
    strategy_lane_coupled BOOLEAN NOT NULL DEFAULT FALSE,
    live_trading_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    execution_authority BOOLEAN NOT NULL DEFAULT FALSE,
    may_submit_order BOOLEAN NOT NULL DEFAULT FALSE,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT execution_lane_commands_mode_check CHECK (lane_mode IN ('paper', 'live')),
    CONSTRAINT execution_lane_commands_status_check CHECK (status IN ('QUEUED', 'CLAIMED', 'REPORTED', 'REJECTED')),
    CONSTRAINT execution_lane_commands_decoupled CHECK (strategy_lane_coupled IS FALSE),
    CONSTRAINT execution_command_submit_requires_live_authority CHECK (
        (live_trading_enabled IS FALSE AND execution_authority IS FALSE AND may_submit_order IS FALSE)
        OR (
            lane_mode = 'live'
            AND live_trading_enabled IS TRUE
            AND execution_authority IS TRUE
            AND may_submit_order IS TRUE
            AND reconciliation_required IS TRUE
            AND promotion_approval_id IS NOT NULL
            AND risk_profile_id IS NOT NULL
            AND credential_slot_ref IS NOT NULL
            AND risk_decision ->> 'status' = 'approved'
        )
    ),
    CONSTRAINT execution_lane_commands_idempotency UNIQUE (runtime_profile_id, idempotency_key)
);

CREATE TABLE IF NOT EXISTS builder.execution_lane_reports (
    execution_lane_report_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    runtime_profile_id TEXT NOT NULL,
    execution_lane_command_id TEXT NOT NULL,
    execution_report_id TEXT,
    lane_mode TEXT NOT NULL,
    report_type TEXT NOT NULL,
    venue TEXT NOT NULL,
    instrument_id TEXT NOT NULL,
    strategy_lane_coupled BOOLEAN NOT NULL DEFAULT FALSE,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT execution_lane_reports_mode_check CHECK (lane_mode IN ('paper', 'live')),
    CONSTRAINT execution_lane_reports_decoupled CHECK (strategy_lane_coupled IS FALSE)
);

CREATE TABLE IF NOT EXISTS builder.execution_lane_heartbeats (
    execution_lane_heartbeat_id BIGSERIAL PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    runtime_profile_id TEXT NOT NULL,
    execution_lane_run_id TEXT,
    worker_id TEXT NOT NULL,
    status TEXT NOT NULL,
    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    strategy_lane_coupled BOOLEAN NOT NULL DEFAULT FALSE,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    CONSTRAINT execution_lane_heartbeats_decoupled CHECK (strategy_lane_coupled IS FALSE)
);

CREATE INDEX IF NOT EXISTS execution_lane_runs_profile_idx ON builder.execution_lane_runs (tenant_id, project_id, runtime_profile_id, status);
CREATE INDEX IF NOT EXISTS execution_lane_commands_queue_idx ON builder.execution_lane_commands (tenant_id, project_id, runtime_profile_id, status, created_at);
CREATE INDEX IF NOT EXISTS execution_lane_commands_trade_action_idx ON builder.execution_lane_commands (tenant_id, project_id, trade_action_id);
CREATE INDEX IF NOT EXISTS execution_lane_reports_command_idx ON builder.execution_lane_reports (tenant_id, project_id, execution_lane_command_id, created_at);
CREATE INDEX IF NOT EXISTS execution_lane_heartbeats_profile_idx ON builder.execution_lane_heartbeats (tenant_id, project_id, runtime_profile_id, last_seen_at);

INSERT INTO builder.schema_migrations (version, description)
VALUES ('003_builder_execution_lane', 'Standalone execution lane queues, reports, and worker heartbeats decoupled from strategy lane')
ON CONFLICT (version) DO NOTHING;
