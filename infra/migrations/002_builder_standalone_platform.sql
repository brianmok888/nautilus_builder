CREATE SCHEMA IF NOT EXISTS builder;

CREATE TABLE IF NOT EXISTS builder.schema_migrations (
    version TEXT PRIMARY KEY,
    description TEXT NOT NULL,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    payload JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS builder.runtime_profiles (
    runtime_profile_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    profile_name TEXT NOT NULL,
    runtime_mode TEXT NOT NULL,
    environment TEXT NOT NULL DEFAULT 'local',
    status TEXT NOT NULL DEFAULT 'draft',
    enabled BOOLEAN NOT NULL DEFAULT FALSE,
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
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT runtime_profiles_runtime_mode_check CHECK (runtime_mode IN ('authoring', 'backtest', 'research', 'optimizer', 'paper', 'live')),
    CONSTRAINT runtime_profiles_environment_check CHECK (environment IN ('local', 'staging', 'testnet', 'paper', 'production')),
    CONSTRAINT live_authority_requires_activation CHECK (
        (live_trading_enabled IS FALSE AND execution_authority IS FALSE AND may_submit_order IS FALSE)
        OR (
            runtime_mode = 'live'
            AND enabled IS TRUE
            AND live_trading_enabled IS TRUE
            AND execution_authority IS TRUE
            AND may_submit_order IS TRUE
            AND advisory_only IS FALSE
            AND manual_review_required IS TRUE
            AND reconciliation_required IS TRUE
            AND risk_profile_id IS NOT NULL
            AND activated_by IS NOT NULL
            AND activated_at IS NOT NULL
            AND NULLIF(config_checksum, '') IS NOT NULL
            AND NULLIF(credential_slot_ref, '') IS NOT NULL
        )
    ),
    CONSTRAINT paper_profile_cannot_enable_live CHECK (
        runtime_mode <> 'paper'
        OR (
            live_trading_enabled IS FALSE
            AND may_submit_order IS FALSE
            AND (paper_trading_enabled IS TRUE OR enabled IS FALSE)
        )
    )
);

CREATE TABLE IF NOT EXISTS builder.strategy_specs (
    strategy_spec_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    strategy_lineage_id TEXT NOT NULL,
    strategy_version_id TEXT NOT NULL,
    parent_strategy_version_id TEXT,
    stage TEXT NOT NULL DEFAULT 'draft',
    status TEXT NOT NULL DEFAULT 'draft',
    compile_hash TEXT,
    strategy_class_path TEXT,
    config_class_path TEXT,
    validation_output_mode TEXT NOT NULL DEFAULT 'signal_preview_only',
    strategy_spec JSONB NOT NULL,
    created_from TEXT NOT NULL DEFAULT 'user',
    created_by TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    CONSTRAINT strategy_specs_stage_check CHECK (stage IN ('draft', 'validated', 'backtested', 'paper_candidate', 'live_candidate', 'retired')),
    CONSTRAINT strategy_specs_output_mode_check CHECK (validation_output_mode IN ('signal_preview_only')),
    CONSTRAINT strategy_specs_unique_version UNIQUE (tenant_id, project_id, strategy_lineage_id, strategy_version_id)
);

CREATE TABLE IF NOT EXISTS builder.strategy_param_versions (
    strategy_param_version_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    strategy_lineage_id TEXT NOT NULL,
    strategy_version_id TEXT NOT NULL,
    parent_strategy_param_version_id TEXT,
    params JSONB NOT NULL,
    params_checksum TEXT NOT NULL,
    created_by TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    payload JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS builder.active_strategy_params (
    active_strategy_params_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    strategy_lineage_id TEXT NOT NULL,
    strategy_version_id TEXT NOT NULL,
    strategy_param_version_id TEXT NOT NULL,
    runtime_profile_id TEXT NOT NULL,
    activated_by TEXT NOT NULL,
    activated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    activation_reason TEXT NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS builder.dataset_manifests (
    dataset_manifest_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    catalog_root_id TEXT NOT NULL,
    catalog_path TEXT NOT NULL,
    source_mode TEXT NOT NULL,
    cache_mode TEXT NOT NULL DEFAULT 'read_only',
    instrument_id TEXT NOT NULL,
    venue TEXT NOT NULL,
    data_type TEXT NOT NULL,
    data_cls TEXT NOT NULL,
    bar_type TEXT,
    start_ts TIMESTAMPTZ NOT NULL,
    end_ts TIMESTAMPTZ NOT NULL,
    manifest_checksum TEXT NOT NULL,
    artifact_ref JSONB NOT NULL DEFAULT '{}'::jsonb,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT dataset_source_mode_check CHECK (source_mode IN ('catalog', 'local_fixture', 'external_mirror_manifest', 'user_fetched_manifest', 'synthetic_test_kit')),
    CONSTRAINT dataset_cache_mode_check CHECK (cache_mode IN ('read_only', 'cache_copy', 'fixture_cache', 'materialized_view')),
    CONSTRAINT dataset_catalog_path_no_traversal CHECK (catalog_path !~ '(^|/)\.\.(/|$)' AND catalog_path !~ '(^|/)\.($|/)'),
    CONSTRAINT dataset_manifest_checksum_required CHECK (NULLIF(manifest_checksum, '') IS NOT NULL),
    CONSTRAINT dataset_time_range_check CHECK (end_ts > start_ts)
);

CREATE TABLE IF NOT EXISTS builder.backtest_jobs (
    backtest_job_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    strategy_lineage_id TEXT NOT NULL,
    strategy_version_id TEXT NOT NULL,
    runtime_profile_id TEXT NOT NULL,
    dataset_manifest_id TEXT NOT NULL,
    engine_mode TEXT NOT NULL DEFAULT 'backtest',
    status TEXT NOT NULL DEFAULT 'queued',
    requested_by TEXT NOT NULL,
    live_trading_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    execution_authority BOOLEAN NOT NULL DEFAULT FALSE,
    may_submit_order BOOLEAN NOT NULL DEFAULT FALSE,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT backtest_jobs_engine_mode_check CHECK (engine_mode IN ('backtest', 'replay_smoke', 'real_engine_smoke')),
    CONSTRAINT backtest_jobs_no_live_authority CHECK (live_trading_enabled IS FALSE AND execution_authority IS FALSE AND may_submit_order IS FALSE)
);

CREATE TABLE IF NOT EXISTS builder.backtest_run_manifests (
    backtest_run_manifest_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    backtest_job_id TEXT NOT NULL,
    strategy_lineage_id TEXT NOT NULL,
    strategy_version_id TEXT NOT NULL,
    compile_hash TEXT NOT NULL,
    dataset_manifest_id TEXT NOT NULL,
    engine_mode TEXT NOT NULL,
    nautilus_trader_version TEXT NOT NULL,
    artifact_manifest_uri TEXT NOT NULL,
    manifest_checksum TEXT NOT NULL,
    started_at TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    CONSTRAINT backtest_manifest_checksum_required CHECK (NULLIF(manifest_checksum, '') IS NOT NULL),
    CONSTRAINT backtest_manifest_compile_hash_required CHECK (NULLIF(compile_hash, '') IS NOT NULL)
);

CREATE TABLE IF NOT EXISTS builder.backtest_artifacts (
    backtest_artifact_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    backtest_run_manifest_id TEXT NOT NULL,
    artifact_scope TEXT NOT NULL,
    artifact_uri TEXT NOT NULL,
    media_type TEXT NOT NULL,
    checksum TEXT NOT NULL,
    checksum_algorithm TEXT NOT NULL DEFAULT 'sha256',
    artifact_kind TEXT NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT backtest_artifact_scope_check CHECK (artifact_scope IN ('project_artifact', 'fixture_dev_only', 'external_mirror_manifest', 'user_fetched_manifest')),
    CONSTRAINT backtest_artifact_uri_no_traversal CHECK (artifact_uri !~ '(^|/)\.\.(/|$)' AND artifact_uri !~ '(^|/)\.($|/)'),
    CONSTRAINT backtest_artifact_uri_scope_check CHECK (
        (artifact_scope = 'fixture_dev_only' AND artifact_uri LIKE 'fixture://%')
        OR (artifact_scope <> 'fixture_dev_only' AND artifact_uri LIKE 'artifact://builder/%')
    ),
    CONSTRAINT backtest_artifact_checksum_required CHECK (NULLIF(checksum, '') IS NOT NULL),
    CONSTRAINT backtest_artifact_media_type_required CHECK (NULLIF(media_type, '') IS NOT NULL),
    CONSTRAINT backtest_artifact_checksum_algorithm_check CHECK (checksum_algorithm IN ('sha256', 'sha512', 'blake3'))
);

CREATE TABLE IF NOT EXISTS builder.research_jobs (
    research_job_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    strategy_lineage_id TEXT NOT NULL,
    strategy_version_id TEXT NOT NULL,
    dataset_manifest_id TEXT NOT NULL,
    runtime_profile_id TEXT,
    job_kind TEXT NOT NULL DEFAULT 'offline_research',
    status TEXT NOT NULL DEFAULT 'queued',
    manual_promotion_required BOOLEAN NOT NULL DEFAULT TRUE,
    may_submit_order BOOLEAN NOT NULL DEFAULT FALSE,
    execution_authority BOOLEAN NOT NULL DEFAULT FALSE,
    requested_by TEXT NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT research_jobs_kind_check CHECK (job_kind IN ('offline_research', 'optimizer', 'walk_forward', 'parameter_sweep')),
    CONSTRAINT research_jobs_no_execution CHECK (may_submit_order IS FALSE AND execution_authority IS FALSE)
);

CREATE TABLE IF NOT EXISTS builder.optimizer_trials (
    optimizer_trial_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    research_job_id TEXT NOT NULL,
    strategy_lineage_id TEXT NOT NULL,
    strategy_version_id TEXT NOT NULL,
    backtest_run_manifest_id TEXT,
    candidate_rank INTEGER,
    params JSONB NOT NULL,
    metrics JSONB NOT NULL DEFAULT '{}'::jsonb,
    status TEXT NOT NULL DEFAULT 'queued',
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT optimizer_trials_rank_positive CHECK (candidate_rank IS NULL OR candidate_rank > 0)
);

CREATE TABLE IF NOT EXISTS builder.ai_threads (
    ai_thread_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    strategy_lineage_id TEXT,
    started_by TEXT NOT NULL,
    provider_name TEXT NOT NULL,
    model_name TEXT NOT NULL,
    purpose TEXT NOT NULL DEFAULT 'strategy_drafting',
    advisory_only BOOLEAN NOT NULL DEFAULT TRUE,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS builder.ai_draft_audits (
    ai_draft_audit_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    strategy_lineage_id TEXT NOT NULL,
    strategy_version_id TEXT NOT NULL,
    ai_thread_id TEXT NOT NULL,
    improvement_cycle_id TEXT NOT NULL,
    prompt_checksum TEXT NOT NULL,
    response_checksum TEXT,
    provider_name TEXT NOT NULL,
    model_name TEXT NOT NULL,
    accepted BOOLEAN NOT NULL DEFAULT FALSE,
    validation_errors JSONB NOT NULL DEFAULT '[]'::jsonb,
    may_submit_order BOOLEAN NOT NULL DEFAULT FALSE,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ai_draft_audits_no_execution CHECK (may_submit_order IS FALSE)
);

CREATE TABLE IF NOT EXISTS builder.ai_result_reviews (
    ai_result_review_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    strategy_lineage_id TEXT NOT NULL,
    strategy_version_id TEXT NOT NULL,
    ai_thread_id TEXT NOT NULL,
    improvement_cycle_id TEXT NOT NULL,
    backtest_run_manifest_id TEXT,
    optimizer_trial_id TEXT,
    review_status TEXT NOT NULL DEFAULT 'pending',
    may_submit_order BOOLEAN NOT NULL DEFAULT FALSE,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ai_result_reviews_no_execution CHECK (may_submit_order IS FALSE)
);

CREATE TABLE IF NOT EXISTS builder.ai_improvement_suggestions (
    ai_improvement_suggestion_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    strategy_lineage_id TEXT NOT NULL,
    strategy_version_id TEXT NOT NULL,
    ai_thread_id TEXT NOT NULL,
    improvement_cycle_id TEXT NOT NULL,
    suggestion_id TEXT NOT NULL,
    suggestion_status TEXT NOT NULL DEFAULT 'proposed',
    candidate_rank INTEGER,
    may_submit_order BOOLEAN NOT NULL DEFAULT FALSE,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ai_improvement_suggestions_no_execution CHECK (may_submit_order IS FALSE)
);

CREATE TABLE IF NOT EXISTS builder.ai_experiment_cycles (
    improvement_cycle_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    strategy_lineage_id TEXT NOT NULL,
    strategy_version_id TEXT NOT NULL,
    ai_thread_id TEXT NOT NULL,
    parent_improvement_cycle_id TEXT,
    backtest_result_id TEXT,
    optimizer_trial_id TEXT,
    status TEXT NOT NULL DEFAULT 'open',
    may_submit_order BOOLEAN NOT NULL DEFAULT FALSE,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ai_experiment_cycles_no_execution CHECK (may_submit_order IS FALSE)
);

CREATE TABLE IF NOT EXISTS builder.ai_candidate_rankings (
    ai_candidate_ranking_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    strategy_lineage_id TEXT NOT NULL,
    strategy_version_id TEXT NOT NULL,
    ai_thread_id TEXT NOT NULL,
    improvement_cycle_id TEXT NOT NULL,
    candidate_strategy_version_id TEXT NOT NULL,
    promotion_candidate_id TEXT,
    candidate_rank INTEGER NOT NULL,
    score NUMERIC,
    may_submit_order BOOLEAN NOT NULL DEFAULT FALSE,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ai_candidate_rankings_rank_positive CHECK (candidate_rank > 0),
    CONSTRAINT ai_candidate_rankings_no_execution CHECK (may_submit_order IS FALSE)
);

CREATE TABLE IF NOT EXISTS builder.ai_feedback_memory (
    ai_feedback_memory_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    strategy_lineage_id TEXT,
    strategy_version_id TEXT,
    source_event_id TEXT,
    memory_kind TEXT NOT NULL,
    embedding_status TEXT NOT NULL DEFAULT 'not_indexed',
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS builder.promotion_candidate_packages (
    promotion_candidate_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    strategy_lineage_id TEXT NOT NULL,
    strategy_version_id TEXT NOT NULL,
    backtest_run_manifest_id TEXT NOT NULL,
    optimizer_trial_id TEXT,
    compile_hash TEXT NOT NULL,
    package_checksum TEXT NOT NULL,
    manual_review_required BOOLEAN NOT NULL DEFAULT TRUE,
    may_submit_order BOOLEAN NOT NULL DEFAULT FALSE,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_by TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT promotion_candidate_package_checksum_required CHECK (NULLIF(package_checksum, '') IS NOT NULL),
    CONSTRAINT promotion_candidate_no_direct_order CHECK (may_submit_order IS FALSE)
);

CREATE TABLE IF NOT EXISTS builder.promotion_approvals (
    promotion_approval_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    promotion_candidate_id TEXT NOT NULL,
    strategy_lineage_id TEXT NOT NULL,
    strategy_version_id TEXT NOT NULL,
    approval_state TEXT NOT NULL DEFAULT 'manual_approval_pending',
    approved_by TEXT,
    approved_at TIMESTAMPTZ,
    target_runtime_mode TEXT NOT NULL DEFAULT 'paper',
    runtime_profile_id TEXT,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT promotion_approvals_state_check CHECK (approval_state IN ('manual_approval_pending', 'approved', 'rejected', 'revoked')),
    CONSTRAINT promotion_approvals_target_mode_check CHECK (target_runtime_mode IN ('paper', 'live'))
);

CREATE TABLE IF NOT EXISTS builder.paper_runs (
    paper_run_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    runtime_profile_id TEXT NOT NULL,
    strategy_lineage_id TEXT NOT NULL,
    strategy_version_id TEXT NOT NULL,
    promotion_candidate_id TEXT,
    simulated_execution BOOLEAN NOT NULL DEFAULT TRUE,
    live_trading_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    may_submit_order BOOLEAN NOT NULL DEFAULT FALSE,
    status TEXT NOT NULL DEFAULT 'created',
    started_by TEXT NOT NULL,
    started_at TIMESTAMPTZ,
    stopped_at TIMESTAMPTZ,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    CONSTRAINT paper_runs_simulated_only CHECK (simulated_execution IS TRUE AND live_trading_enabled IS FALSE AND may_submit_order IS FALSE)
);

CREATE TABLE IF NOT EXISTS builder.live_runs (
    live_run_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    runtime_profile_id TEXT NOT NULL,
    strategy_lineage_id TEXT NOT NULL,
    strategy_version_id TEXT NOT NULL,
    promotion_candidate_id TEXT,
    risk_profile_id TEXT NOT NULL,
    reconciliation_required BOOLEAN NOT NULL DEFAULT TRUE,
    credential_slot_ref TEXT NOT NULL,
    live_trading_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    execution_authority BOOLEAN NOT NULL DEFAULT FALSE,
    may_submit_order BOOLEAN NOT NULL DEFAULT FALSE,
    status TEXT NOT NULL DEFAULT 'created',
    started_by TEXT,
    started_at TIMESTAMPTZ,
    stopped_at TIMESTAMPTZ,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    CONSTRAINT live_run_requires_profile_authority CHECK (
        (live_trading_enabled IS FALSE AND execution_authority IS FALSE AND may_submit_order IS FALSE)
        OR (
            live_trading_enabled IS TRUE
            AND execution_authority IS TRUE
            AND may_submit_order IS TRUE
            AND reconciliation_required IS TRUE
            AND NULLIF(risk_profile_id, '') IS NOT NULL
            AND NULLIF(credential_slot_ref, '') IS NOT NULL
            AND started_by IS NOT NULL
            AND started_at IS NOT NULL
        )
    )
);

CREATE TABLE IF NOT EXISTS builder.trade_actions (
    trade_action_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    runtime_profile_id TEXT NOT NULL,
    live_run_id TEXT,
    promotion_approval_id TEXT,
    risk_profile_id TEXT,
    reconciliation_required BOOLEAN NOT NULL DEFAULT TRUE,
    strategy_lineage_id TEXT NOT NULL,
    strategy_version_id TEXT NOT NULL,
    source_event_id TEXT,
    order_intent JSONB NOT NULL,
    risk_decision JSONB NOT NULL DEFAULT '{}'::jsonb,
    live_trading_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    execution_authority BOOLEAN NOT NULL DEFAULT FALSE,
    may_submit_order BOOLEAN NOT NULL DEFAULT FALSE,
    status TEXT NOT NULL DEFAULT 'pending_risk_review',
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT trade_action_submit_requires_live_authority CHECK (
        (live_trading_enabled IS FALSE AND execution_authority IS FALSE AND may_submit_order IS FALSE)
        OR (
            live_trading_enabled IS TRUE
            AND execution_authority IS TRUE
            AND may_submit_order IS TRUE
            AND reconciliation_required IS TRUE
            AND live_run_id IS NOT NULL
            AND promotion_approval_id IS NOT NULL
            AND risk_profile_id IS NOT NULL
            AND status = 'risk_approved'
        )
    )
);

CREATE TABLE IF NOT EXISTS builder.execution_reports (
    execution_report_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    runtime_profile_id TEXT NOT NULL,
    trade_action_id TEXT,
    live_run_id TEXT,
    paper_run_id TEXT,
    strategy_lineage_id TEXT NOT NULL,
    strategy_version_id TEXT NOT NULL,
    order_id TEXT,
    venue TEXT NOT NULL,
    instrument_id TEXT NOT NULL,
    report_type TEXT NOT NULL,
    event_ts TIMESTAMPTZ NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS builder.telegram_users (
    telegram_user_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    telegram_chat_id TEXT NOT NULL,
    telegram_username TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT telegram_users_telegram_chat_id_key UNIQUE (telegram_chat_id)
);

CREATE TABLE IF NOT EXISTS builder.telegram_subscriptions (
    telegram_subscription_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    telegram_user_id TEXT NOT NULL,
    subscription_kind TEXT NOT NULL,
    runtime_profile_id TEXT,
    strategy_lineage_id TEXT,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    notification_only BOOLEAN NOT NULL DEFAULT TRUE,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT telegram_subscriptions_notification_only CHECK (notification_only IS TRUE)
);

CREATE TABLE IF NOT EXISTS builder.telegram_delivery_log (
    telegram_delivery_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    telegram_user_id TEXT,
    telegram_subscription_id TEXT,
    event_type TEXT NOT NULL,
    notification_only BOOLEAN NOT NULL DEFAULT TRUE,
    delivery_status TEXT NOT NULL DEFAULT 'queued',
    message_checksum TEXT,
    provider_message_id TEXT,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    delivered_at TIMESTAMPTZ,
    CONSTRAINT telegram_delivery_notification_only CHECK (notification_only IS TRUE)
);

ALTER TABLE builder.runtime_events
    ADD COLUMN IF NOT EXISTS tenant_id TEXT,
    ADD COLUMN IF NOT EXISTS project_id TEXT,
    ADD COLUMN IF NOT EXISTS runtime_profile_id TEXT,
    ADD COLUMN IF NOT EXISTS event_type TEXT,
    ADD COLUMN IF NOT EXISTS stream_name TEXT,
    ADD COLUMN IF NOT EXISTS source_component TEXT,
    ADD COLUMN IF NOT EXISTS strategy_lineage_id TEXT,
    ADD COLUMN IF NOT EXISTS strategy_version_id TEXT;

CREATE INDEX IF NOT EXISTS runtime_profiles_tenant_project_idx ON builder.runtime_profiles (tenant_id, project_id, runtime_mode, enabled);
CREATE INDEX IF NOT EXISTS strategy_specs_lineage_idx ON builder.strategy_specs (tenant_id, project_id, strategy_lineage_id, strategy_version_id);
CREATE INDEX IF NOT EXISTS dataset_manifests_instrument_idx ON builder.dataset_manifests (tenant_id, project_id, instrument_id, venue, data_type);
CREATE INDEX IF NOT EXISTS backtest_jobs_strategy_idx ON builder.backtest_jobs (tenant_id, project_id, strategy_lineage_id, strategy_version_id, status);
CREATE INDEX IF NOT EXISTS backtest_artifacts_manifest_idx ON builder.backtest_artifacts (tenant_id, project_id, backtest_run_manifest_id, artifact_kind);
CREATE INDEX IF NOT EXISTS research_jobs_strategy_idx ON builder.research_jobs (tenant_id, project_id, strategy_lineage_id, strategy_version_id, status);
CREATE INDEX IF NOT EXISTS optimizer_trials_rank_idx ON builder.optimizer_trials (research_job_id, candidate_rank);
CREATE INDEX IF NOT EXISTS ai_threads_strategy_idx ON builder.ai_threads (tenant_id, project_id, strategy_lineage_id);
CREATE INDEX IF NOT EXISTS ai_draft_audits_cycle_idx ON builder.ai_draft_audits (ai_thread_id, improvement_cycle_id, accepted);
CREATE INDEX IF NOT EXISTS ai_candidate_rankings_rank_idx ON builder.ai_candidate_rankings (tenant_id, project_id, improvement_cycle_id, candidate_rank);
CREATE INDEX IF NOT EXISTS promotion_candidate_strategy_idx ON builder.promotion_candidate_packages (tenant_id, project_id, strategy_lineage_id, strategy_version_id);
CREATE INDEX IF NOT EXISTS promotion_approvals_state_idx ON builder.promotion_approvals (tenant_id, project_id, approval_state, target_runtime_mode);
CREATE INDEX IF NOT EXISTS paper_runs_profile_idx ON builder.paper_runs (tenant_id, project_id, runtime_profile_id, status);
CREATE INDEX IF NOT EXISTS live_runs_profile_idx ON builder.live_runs (tenant_id, project_id, runtime_profile_id, status);
CREATE INDEX IF NOT EXISTS execution_reports_strategy_idx ON builder.execution_reports (tenant_id, project_id, strategy_lineage_id, strategy_version_id, event_ts);
CREATE INDEX IF NOT EXISTS telegram_delivery_status_idx ON builder.telegram_delivery_log (tenant_id, project_id, delivery_status, created_at);
CREATE INDEX IF NOT EXISTS runtime_events_profile_idx ON builder.runtime_events (tenant_id, project_id, runtime_profile_id, event_type);

INSERT INTO builder.schema_migrations (version, description)
VALUES ('002_builder_standalone_platform', 'Standalone Builder control-plane schema for AI, backtest, research, paper/live, and Telegram lanes')
ON CONFLICT (version) DO NOTHING;
