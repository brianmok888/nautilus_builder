import type { AdapterSummary, AiDraftApplication, AiDraftPayload, AiDraftResult, BackendHealth, BacktestJobEvents, BacktestJobStatus, BacktestProfileValidation, DataAvailability, InstrumentSummary, PromotionRequestResult, ResultDashboardPayload, StrategyDetail, StrategyRecord, StrategySummary } from "./types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "";

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly payload: unknown,
  ) {
    super(message);
  }
}

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, init);
  const payload = await response.json();
  if (!response.ok) {
    throw new ApiError("Nautilus Builder API request failed", response.status, payload);
  }
  return payload as T;
}

export async function fetchBackendHealth(): Promise<BackendHealth> {
  return apiFetch<BackendHealth>("/health/backend");
}

export async function fetchAdapters(): Promise<AdapterSummary[]> {
  return apiFetch<AdapterSummary[]>("/api/adapters");
}

export async function fetchStrategies(): Promise<StrategySummary[]> {
  return apiFetch<StrategySummary[]>("/api/strategies");
}

export async function createStrategy(spec: Record<string, unknown>): Promise<StrategyRecord> {
  return apiFetch<StrategyRecord>("/api/strategies", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(spec) });
}

export async function fetchStrategyDetail(strategyId: string): Promise<StrategyDetail> {
  return apiFetch<StrategyDetail>(`/api/strategies/${strategyId}`);
}

export async function fetchInstruments(adapter_id: string, query: string): Promise<InstrumentSummary[]> {
  const params = new URLSearchParams({ adapter_id, query });
  return apiFetch<InstrumentSummary[]>(`/api/instruments?${params.toString()}`);
}

export async function fetchDataAvailability(adapter_id: string, instrument_id: string): Promise<DataAvailability> {
  const params = new URLSearchParams({ adapter_id, instrument_id });
  return apiFetch<DataAvailability>(`/api/data-availability/${adapter_id}/${instrument_id}?${params.toString()}`);
}

export async function createBacktestJob(payload: Record<string, string>): Promise<BacktestJobStatus> {
  return apiFetch<BacktestJobStatus>("/api/backtest-jobs", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
}

export async function fetchBacktestJob(jobId: string): Promise<BacktestJobStatus> {
  return apiFetch<BacktestJobStatus>(`/api/backtest-jobs/${jobId}`);
}

export async function cancelBacktestJob(jobId: string): Promise<BacktestJobStatus> {
  return apiFetch<BacktestJobStatus>(`/api/backtest-jobs/${jobId}/cancel`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({}) });
}

export async function fetchBacktestJobEvents(jobId: string): Promise<BacktestJobEvents> {
  return apiFetch<BacktestJobEvents>(`/api/backtest-jobs/${jobId}/events`);
}

export async function fetchResultSummary(resultId: string): Promise<ResultDashboardPayload> {
  return apiFetch<ResultDashboardPayload>(`/api/results/${resultId}`);
}

export async function fetchResultArtifacts(resultId: string): Promise<Record<string, unknown>> {
  return (await fetchResultSummary(resultId)).artifacts;
}

export async function fetchResultTrades(resultId: string): Promise<unknown[]> {
  return (await fetchResultSummary(resultId)).trades;
}

export async function fetchResultFills(resultId: string): Promise<unknown[]> {
  return (await fetchResultSummary(resultId)).fills;
}

export async function generateAiDraft(payload: AiDraftPayload): Promise<AiDraftResult> {
  return apiFetch<AiDraftResult>("/api/ai-builder/draft", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
}

export async function applyAiDraftToBuilder(payload: AiDraftPayload): Promise<AiDraftApplication> {
  return apiFetch<AiDraftApplication>("/api/ai-builder/apply", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
}

export async function requestShadowPromotion(payload: { strategy_version_id: string; result_id: string; target: "shadow" | "signal-preview" }): Promise<PromotionRequestResult> {
  return apiFetch<PromotionRequestResult>("/api/promotions/request", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
}

export async function validateBacktestProfile(profile: Record<string, string>): Promise<BacktestProfileValidation> {
  return apiFetch<BacktestProfileValidation>("/api/backtest-profiles/validate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(profile),
  });
}
