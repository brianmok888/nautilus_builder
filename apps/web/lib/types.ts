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
  venue_bindings: ExecutionLaneVenueBinding[];
  ui_features: ExecutionLaneUiFeatures;
  strategy_lane_coupled: false;
  may_submit_order: boolean;
};

export type BackendHealth = {
  status: string;
  service: string;
};

export type StrategySummary = {
  strategy_id: string;
  strategy_lineage_id: string;
  latest_spec: Record<string, unknown>;
};

export type StrategyRecord = {
  strategy_id: string;
  strategy_lineage_id: string;
  strategy_version_id: string;
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
  mode?: string;
};

export type BacktestJobEvents = {
  job_id: string;
  stream_name: string;
  status?: string;
  mode: "observational";
  events: unknown[];
};

export type ReportSummary = {
  metrics: Record<string, unknown>;
  sections: string[];
  chart_sections: string[];
  live_trading_enabled: false;
  execution_authority: false;
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
