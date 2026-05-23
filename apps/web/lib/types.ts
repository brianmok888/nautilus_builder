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
  name: string;
  venue: string;
};

export type BacktestProfileValidation = {
  valid: boolean;
  instrument?: Record<string, unknown>;
  error?: string;
  adapter_profile_id?: string;
};

export type InstrumentSummary = {
  instrument_id: string;
  adapter_id: string;
  symbol: string;
};

export type DataAvailability = {
  instrument_id: string;
  adapter_id?: string;
  supported_timeframes?: string[];
  available_timeframes?: string[];
  available_date_ranges?: Array<{ start: string; end: string }>;
};

export type BacktestJobStatus = {
  job_id: string;
  status: string;
  mode?: string;
};

export type BacktestJobEvents = {
  job_id: string;
  stream_name: string;
  mode: "observational";
  events: unknown[];
};

export type ResultDashboardPayload = {
  result_id: string;
  metrics: Record<string, unknown>;
  artifacts: Record<string, unknown>;
  trades: unknown[];
  fills: unknown[];
  logs: unknown[];
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
