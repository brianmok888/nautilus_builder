CREATE SCHEMA IF NOT EXISTS builder;

ALTER TABLE builder.execution_lane_runs
    ADD COLUMN IF NOT EXISTS enabled BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS adapter_id TEXT,
    ADD COLUMN IF NOT EXISTS venue TEXT,
    ADD COLUMN IF NOT EXISTS venue_account_id TEXT,
    ADD COLUMN IF NOT EXISTS ui_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS paper_controls_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS live_controls_enabled BOOLEAN NOT NULL DEFAULT FALSE;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'execution_lane_runs_enabled_requires_venue'
          AND conrelid = 'builder.execution_lane_runs'::regclass
    ) THEN
        ALTER TABLE builder.execution_lane_runs
            ADD CONSTRAINT execution_lane_runs_enabled_requires_venue CHECK (
                enabled IS FALSE
                OR (
                    NULLIF(adapter_id, '') IS NOT NULL
                    AND NULLIF(venue, '') IS NOT NULL
                )
            ) NOT VALID;
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'execution_lane_runs_live_ui_requires_authority'
          AND conrelid = 'builder.execution_lane_runs'::regclass
    ) THEN
        ALTER TABLE builder.execution_lane_runs
            ADD CONSTRAINT execution_lane_runs_live_ui_requires_authority CHECK (
                live_controls_enabled IS FALSE
                OR (
                    lane_mode = 'live'
                    AND enabled IS TRUE
                    AND live_trading_enabled IS TRUE
                    AND execution_authority IS TRUE
                    AND may_submit_order IS TRUE
                    AND advisory_only IS FALSE
                    AND manual_review_required IS TRUE
                    AND reconciliation_required IS TRUE
                    AND NULLIF(risk_profile_id, '') IS NOT NULL
                    AND NULLIF(credential_slot_ref, '') IS NOT NULL
                    AND activated_by IS NOT NULL
                    AND activated_at IS NOT NULL
                    AND NULLIF(config_checksum, '') IS NOT NULL
                )
            ) NOT VALID;
    END IF;
END $$;

ALTER TABLE builder.execution_lane_commands
    ADD COLUMN IF NOT EXISTS adapter_id TEXT,
    ADD COLUMN IF NOT EXISTS venue TEXT,
    ADD COLUMN IF NOT EXISTS venue_account_id TEXT;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'execution_lane_commands_require_venue'
          AND conrelid = 'builder.execution_lane_commands'::regclass
    ) THEN
        ALTER TABLE builder.execution_lane_commands
            ADD CONSTRAINT execution_lane_commands_require_venue CHECK (
                NULLIF(adapter_id, '') IS NOT NULL
                AND NULLIF(venue, '') IS NOT NULL
            ) NOT VALID;
    END IF;
END $$;

ALTER TABLE builder.execution_lane_reports
    ADD COLUMN IF NOT EXISTS adapter_id TEXT,
    ADD COLUMN IF NOT EXISTS venue_account_id TEXT;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'execution_lane_reports_require_adapter'
          AND conrelid = 'builder.execution_lane_reports'::regclass
    ) THEN
        ALTER TABLE builder.execution_lane_reports
            ADD CONSTRAINT execution_lane_reports_require_adapter CHECK (
                NULLIF(adapter_id, '') IS NOT NULL
            ) NOT VALID;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS execution_lane_runs_venue_idx
    ON builder.execution_lane_runs (tenant_id, project_id, adapter_id, venue, runtime_profile_id, status);

CREATE INDEX IF NOT EXISTS execution_lane_commands_venue_idx
    ON builder.execution_lane_commands (tenant_id, project_id, adapter_id, venue, status, created_at);

CREATE INDEX IF NOT EXISTS execution_lane_reports_venue_idx
    ON builder.execution_lane_reports (tenant_id, project_id, adapter_id, venue, created_at);

INSERT INTO builder.schema_migrations (version, description)
VALUES ('004_builder_execution_lane_venue_ui', 'Bind execution lanes and commands to adapter venues and UI feature flags')
ON CONFLICT (version) DO NOTHING;
