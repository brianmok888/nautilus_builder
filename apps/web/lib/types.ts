export type BackendHealth = {
  status: string;
  service: string;
};

export type StrategySummary = {
  strategy_id: string;
  strategy_lineage_id: string;
  latest_spec: Record<string, unknown>;
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
  available_timeframes?: string[];
};
