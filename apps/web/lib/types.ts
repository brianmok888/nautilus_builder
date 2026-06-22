export type ExecutionLaneVenueBinding = {
  runtime_profile_id: string;
  adapter_id: string;
  venue: string;
  venue_account_id?: string | null;
  lane_mode: "paper" | "live" | string;
  enabled: boolean;
};

export type ExecutionLaneUiFeatures = {
  execution_lane_ui_enabled: boolean;
  paper_controls_enabled: boolean;
  live_controls_enabled: boolean;
  credential_inputs_allowed: false;
  strategy_lane_coupled: false;
};

export type ExecutionLaneStatus = {
  mode: "execution_lane" | string;
  runtime_profile_id: string | null;
  profiles?: number;
  queued_commands?: number;
  claimed_commands?: number;
  reported_commands?: number;
  reports?: number;
  sessions?: number;
  running_sessions?: number;
  credential_slots?: number;
  venue_bindings: ExecutionLaneVenueBinding[];
  ui_features: ExecutionLaneUiFeatures;
  strategy_lane_coupled: false;
  may_submit_order: boolean;
};


export type ExecutionLaneProfile = {
  tenant_id: string;
  project_id: string;
  runtime_profile_id: string;
  profile_name: string;
  lane_mode: "paper" | "live";
  enabled: boolean;
  consumes_stream: string;
  adapter_id?: string | null;
  venue?: string | null;
  venue_account_id?: string | null;
  ui_enabled?: boolean;
  paper_controls_enabled?: boolean;
  live_controls_enabled?: boolean;
  paper_trading_enabled?: boolean;
  live_trading_enabled?: boolean;
  execution_authority?: boolean;
  may_submit_order?: boolean;
  strategy_lane_coupled?: false;
};

export type ExecutionLaneRuntimePlan = {
  schema_version: "execution_lane.tradingnode.v1" | string;
  tenant_id: string;
  project_id: string;
  runtime_profile_id: string;
  lane_mode: "paper" | "live" | string;
  readiness_status: "READY" | "BLOCKED" | string;
  blocked_reasons: string[];
  node_runtime: "python_trading_node" | string;
  runtime_label: "python_live_integration_specific" | string;
  future_runtime: "rust_live_node" | string;
  runtime_environment: "sandbox" | "live" | string;
  adapter_id: string;
  venue: string;
  venue_account_id?: string | null;
  strategy_lane_coupled: false;
  browser_credentials_allowed: false;
  credential_inputs_allowed: false;
  live_trading_enabled: boolean;
  execution_authority: boolean;
  may_submit_order: boolean;
  credential_slot_ref?: string | null;
  evidence_refs?: Record<string, string>;
  nautilus_imports?: string[];
  config_contract: Record<string, unknown>;
  nautilus_trader_version?: string | null;
};


export type BackendHealth = {
  status: string;
  service: string;
};

export type StrategyStatus = "draft" | "validated" | "backtested" | "approved" | "execution_ready";

export type StrategySummary = {
  strategy_id: string;
  strategy_lineage_id: string;
  status: StrategyStatus;
  latest_spec: Record<string, unknown>;
};

export type StrategyRecord = {
  strategy_id: string;
  strategy_lineage_id: string;
  strategy_version_id: string;
  status: StrategyStatus;
  spec: Record<string, unknown>;
};

export type StrategyDetail = {
  strategy_id: string;
  strategy_lineage_id: string;
  versions: Array<{ strategy_version_id: string; spec: Record<string, unknown> }>;
};

export type AdapterSummary = {
  adapter_id: string;
  enabled: boolean;
  venue: string;
  asset_class: string;
  data_modes: string[];
  execution_modes: Record<string, boolean>;
};

export type InstrumentSummary = {
  instrument_id: string;
  market_type: string;
  supported_data_types: string[];
  supported_timeframes: string[];
  available_date_ranges: string[];
};

export type DataAvailability = InstrumentSummary;

export type BacktestProfileValidation = {
  valid: boolean;
  instrument?: InstrumentSummary;
  error?: string;
};

export type BacktestJobStatus = {
  job_id: string;
  status: string;
  stage?: string;
  lifecycle_status?: string;
  created_by?: string;
  created_at?: string;
  updated_at?: string;
  strategy_spec_version_id?: string;
  adapter_profile_id?: string;
  instrument_id?: string;
  data_range?: string;
  data_type?: string;
  timeframe?: string;
  market_type?: string;
  worker_id?: string;
  result_artifact_refs?: Record<string, string>;
  event_stream_id?: string;
  cancel_requested?: boolean;
  compile_hash?: string;
  compile_artifact_id?: string;
  dataset_id?: string;
  catalog_path?: string | null;
  mode?: string;
};

export type RuntimeEvent = {
  event_id?: string;
  job_id?: string;
  actor_type?: string;
  actor_id?: string;
  stage: string;
  level?: string;
  message?: string;
  timestamp?: string;
  metadata?: Record<string, unknown>;
  progress_pct?: number;
};

export type BacktestJobEvents = {
  job_id: string;
  stream_name: string;
  status?: string;
  mode: "observational";
  events: RuntimeEvent[];
};

export type BacktestRunResponse = {
  mode: "backend_owned_backtestnode" | string;
  job: BacktestJobStatus;
  result: Record<string, unknown> | null;
  events: RuntimeEvent[];
};

export type ReportSummary = {
  metrics: Record<string, unknown>;
  sections: string[];
  chart_sections: string[];
  live_trading_enabled: false;
  execution_authority: false;
};

export type ResultListItem = {
  result_id: string;
  strategy_lineage_id: string;
  strategy_version_id: string;
  test_job_id: string;
  metrics: Record<string, unknown>;
  created_at: string;
};

export type ResultDashboardPayload = {
  result_id: string;
  metrics: Record<string, unknown>;
  artifacts: Record<string, unknown>;
  trades: unknown[];
  fills: unknown[];
  logs: unknown[];
  report_summary?: ReportSummary;
};


export type LlmConfig = {
  provider_type: string;
  base_url: string;
  roles: {
    draft_strategy_spec: string;
    validate_and_repair: string;
    explain_operator_feedback: string;
  };
  guardrails: Record<string, unknown>;
  credential_inputs_allowed: false;
  secrets_storage: "server_environment";
};

export type LlmConfigSavePayload = {
  provider_type: string;
  base_url: string;
  draft_model: string;
  validation_model: string;
  explanation_model: string;
};

export type AiDraftPayload = {
  prompt: string;
  ai_thread_id: string;
  improvement_cycle_id?: string;
  strategy_lineage_id?: string;
  strategy_version_id?: string;
  spec?: Record<string, unknown>;
};

export type AiDraftResult = {
  spec: Record<string, unknown>;
  accepted: boolean;
  validation_errors: string[];
  explanation: string;
};

export type AiDraftApplication = {
  ai_thread_id: string;
  improvement_cycle_id: string;
  strategy_lineage_id: string;
  strategy_version_id: string;
  stage: "draft";
  mode: "advisory_only";
  spec: Record<string, unknown>;
};

export type PromotionRequestResult = {
  strategy_version_id: string;
  result_id: string;
  target: "shadow" | "signal-preview";
  manual_approval_required: boolean;
};

export type StrategyEvidenceSummary = {
  strategyId: string;
  strategyVersionId: string;
  strategyStatus: string;
  validation: {
    status: string;
    flags: Record<string, unknown>;
  };
  compile: {
    status: string;
    hash: string | null;
    artifactId: string | null;
  };
  replay: {
    status: string;
    jobs: Array<{
      jobId: string;
      status: string;
      stage: string;
      lifecycleStatus: string;
      createdAt: string;
      updatedAt: string;
      compileHash: string;
      compileArtifactId: string | null;
      resultArtifactRefs: Record<string, string>;
      datasetId: string;
    }>;
  };
  promotion: {
    status: string;
  };
  audit: Array<{
    id: string;
    kind: string;
    title: string;
    status: string;
    refId?: string;
    hash?: string;
    timestamp?: string;
  }>;
};

/** Which statuses each lane can see */
export const LANE_ALLOWED_STATUSES: Record<"builder" | "backtest" | "execution", StrategyStatus[]> = {
  builder: ["draft", "validated", "backtested", "approved", "execution_ready"],
  backtest: ["validated", "backtested", "approved", "execution_ready"],
  execution: ["approved", "execution_ready"],
};





/** Color mapping for strategy status chips */
export const STRATEGY_STATUS_COLORS: Record<StrategyStatus, string> = {
  draft: "default",
  validated: "blue",
  backtested: "purple",
  approved: "green",
  execution_ready: "gold",
};


// ─── Frontend/backend read-only reconciliation types ─────────────────────────
// Added to reconnect safe observational backend routes that previously had no
// api.ts helper. These are read-only surfaces only; no execution/order-submit
// endpoints are wired to the frontend. Execution-lane SESSION lifecycle is
// deliberately excluded entirely (backend authority): the UI must not model or
// drive sessions (see tests/web/test_execution_lane_ui_contract.py).

/** Readiness capability entry — mirrors packages.readiness.models.ReadinessEntry. */
export interface ReadinessEntry {
  capability: string;
  status: "ready" | "partial" | "blocked" | "out_of_scope";
  required_evidence_types: string[];
  blocking_reasons: string[];
  last_verified_at?: string | null;
  verified_by_command?: string | null;
}

/** Readiness matrix — mirrors packages.readiness.models.ReadinessMatrix. */
export interface ReadinessMatrix {
  builder_version: string;
  checked_at: string;
  entries: ReadinessEntry[];
}

/** Evidence record — read-only view of a promotion/verification evidence entry. */
export interface EvidenceRecord {
  [field: string]: unknown;
}

/** Runtime-events replay payload (observational; job-timeline replay). */
export interface RuntimeEventsReplay {
  [field: string]: unknown;
}

