import type {
  AdapterSummary,
  AiDraftApplication,
  AiDraftPayload,
  AiDraftResult,
  BackendHealth,
  BacktestJobEvents,
  BacktestJobStatus,
  BacktestRunResponse,
  BacktestProfileValidation,
  DataAvailability,
  ExecutionCredentialSlot,
  ExecutionCredentialSlotRequest,
  ExecutionLaneCommand,
  ExecutionLaneProfile,
  ExecutionLaneReport,
  ExecutionLaneRuntimePlan,
  ExecutionLaneSession,
  ExecutionLaneStatus,
  InstrumentSummary,
  LlmConfig,
  LlmConfigSavePayload,
  PromotionRequestResult,
  ResultDashboardPayload,
  StrategyDetail,
  StrategyRecord,
  StrategySummary,
} from "./types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "";
const DEFAULT_SERVER_API_BASE_URL =
  process.env.BUILDER_API_BASE_URL ?? "http://127.0.0.1:8000";

function apiUrl(path: string): string {
  if (API_BASE_URL) return `${API_BASE_URL}${path}`;
  if (typeof window === "undefined")
    return `${DEFAULT_SERVER_API_BASE_URL}${path}`;
  return path;
}

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly payload: unknown,
    public readonly url: string,
    public readonly contentType = "",
  ) {
    super(message);
    this.name = "ApiError";
  }
}

function responseSnippet(body: string): string {
  return body.length > 240 ? `${body.slice(0, 240)}…` : body;
}

function errorMessage(
  status: number,
  url: string,
  contentType: string,
  body: string,
): string {
  if (!body) {
    return `Nautilus Builder API request failed (${status}) for ${url}: empty response body. Check BUILDER_API_BASE_URL / NEXT_PUBLIC_API_BASE_URL and the VM API proxy.`;
  }
  if (!contentType.toLowerCase().includes("json")) {
    return `Nautilus Builder API request failed (${status}) for ${url}: expected JSON but received ${contentType || "unknown content type"}. Check API base URL/proxy routing. Body: ${responseSnippet(body)}`;
  }
  return `Nautilus Builder API request failed (${status}) for ${url}`;
}

async function parseResponseBody(response: Response): Promise<unknown> {
  const body = await response.text();
  const contentType = response.headers.get("content-type") ?? "";
  const trimmed = body.trim();
  const looksLikeJson = trimmed.startsWith("{") || trimmed.startsWith("[");
  if (!body) return undefined;
  if (!contentType.toLowerCase().includes("json") && !looksLikeJson)
    return { body: responseSnippet(body) };
  try {
    return JSON.parse(body);
  } catch (error) {
    return {
      body: responseSnippet(body),
      parse_error: error instanceof Error ? error.message : String(error),
    };
  }
}

function builderApiToken(): string {
  return (
    process.env.BUILDER_API_TOKEN ??
    process.env.NEXT_PUBLIC_BUILDER_API_TOKEN ??
    ""
  ).trim();
}

function requestInitWithAuth(path: string, init?: RequestInit): RequestInit {
  const headers = new Headers(init?.headers);
  const token = builderApiToken();
  if (path.startsWith("/api/") && token && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  return { ...init, headers };
}

function isAuthErrorPayload(payload: unknown): boolean {
  if (typeof payload !== "object" || payload === null) return false;
  const error = String((payload as { error?: unknown }).error ?? "");
  return error === "auth_required" || error === "invalid_auth_token";
}

export async function apiFetch<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  const url = apiUrl(path);
  const requestInit = requestInitWithAuth(path, init);
  let response: Response;
  try {
    response = await fetch(url, requestInit);
  } catch (error) {
    const cause = error instanceof Error ? error.message : String(error);
    throw new ApiError(
      `Unable to reach Nautilus Builder API at ${url}. Check BUILDER_API_BASE_URL / NEXT_PUBLIC_API_BASE_URL and VM firewall/proxy settings. Cause: ${cause}`,
      0,
      { cause },
      url,
    );
  }

  const payload = await parseResponseBody(response);
  const contentType = response.headers.get("content-type") ?? "";
  if (!response.ok) {
    const body =
      typeof payload === "object" && payload !== null && "body" in payload
        ? String((payload as { body: unknown }).body)
        : "";
    const message = isAuthErrorPayload(payload)
      ? `Nautilus Builder API authentication failed (${response.status}) for ${url}. Configure BUILDER_API_TOKEN or NEXT_PUBLIC_BUILDER_API_TOKEN for local VM/API proxy mode.`
      : body || payload === undefined
        ? errorMessage(response.status, url, contentType, body)
        : `Nautilus Builder API request failed (${response.status}) for ${url}`;
    throw new ApiError(message, response.status, payload, url, contentType);
  }
  return payload as T;
}

export async function fetchBackendHealth(): Promise<BackendHealth> {
  return apiFetch<BackendHealth>("/health/backend");
}

export async function fetchExecutionLaneStatus(
  runtimeProfileId?: string,
): Promise<ExecutionLaneStatus> {
  const params = runtimeProfileId
    ? `?${new URLSearchParams({ runtime_profile_id: runtimeProfileId }).toString()}`
    : "";
  return apiFetch<ExecutionLaneStatus>(`/api/execution-lane/status${params}`);
}

export async function saveExecutionLaneCredentialSlot(
  payload: ExecutionCredentialSlotRequest,
): Promise<ExecutionCredentialSlot> {
  return apiFetch<ExecutionCredentialSlot>("/api/execution-lane/credential-slots", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function registerExecutionLaneProfile(
  payload: Record<string, unknown>,
): Promise<ExecutionLaneProfile> {
  return apiFetch<ExecutionLaneProfile>("/api/execution-lane/profiles", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function fetchExecutionLaneRuntimePlan(
  runtimeProfileId: string,
  commandId?: string,
): Promise<ExecutionLaneRuntimePlan> {
  const params = new URLSearchParams({ runtime_profile_id: runtimeProfileId });
  if (commandId) params.set("command_id", commandId);
  return apiFetch<ExecutionLaneRuntimePlan>(`/api/execution-lane/runtime-plan?${params.toString()}`);
}

export async function enqueueExecutionLaneCommand(
  payload: Record<string, unknown>,
): Promise<ExecutionLaneCommand> {
  return apiFetch<ExecutionLaneCommand>("/api/execution-lane/commands", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function runExecutionLaneWorkerOnce(payload: {
  runtime_profile_id: string;
  worker_id?: string;
}): Promise<ExecutionLaneReport> {
  return apiFetch<ExecutionLaneReport>("/api/execution-lane/worker/run-once", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}


export async function startExecutionLanePaperSession(payload: {
  runtime_profile_id: string;
  command_id: string;
  worker_id?: string;
  project_id?: string;
}): Promise<ExecutionLaneSession> {
  return apiFetch<ExecutionLaneSession>("/api/execution-lane/sessions/start", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function fetchExecutionLaneSession(
  sessionId: string,
): Promise<ExecutionLaneSession> {
  return apiFetch<ExecutionLaneSession>(`/api/execution-lane/sessions/${sessionId}`);
}

export async function stopExecutionLaneSession(
  sessionId: string,
  payload: { worker_id?: string } = {},
): Promise<ExecutionLaneSession> {
  return apiFetch<ExecutionLaneSession>(`/api/execution-lane/sessions/${sessionId}/stop`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function fetchAdapters(): Promise<AdapterSummary[]> {
  return apiFetch<AdapterSummary[]>("/api/adapters");
}

export async function fetchStrategies(): Promise<StrategySummary[]> {
  return apiFetch<StrategySummary[]>("/api/strategies");
}

export async function createStrategy(
  spec: Record<string, unknown>,
): Promise<StrategyRecord> {
  return apiFetch<StrategyRecord>("/api/strategies", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(spec),
  });
}

export async function fetchStrategyDetail(
  strategyId: string,
): Promise<StrategyDetail> {
  return apiFetch<StrategyDetail>(`/api/strategies/${strategyId}`);
}

export async function fetchInstruments(
  adapter_id: string,
  query: string,
): Promise<InstrumentSummary[]> {
  const params = new URLSearchParams({ adapter_id, query });
  return apiFetch<InstrumentSummary[]>(`/api/instruments?${params.toString()}`);
}

export async function fetchDataAvailability(
  adapter_id: string,
  instrument_id: string,
): Promise<DataAvailability> {
  const params = new URLSearchParams({ adapter_id, instrument_id });
  return apiFetch<DataAvailability>(
    `/api/data-availability/${adapter_id}/${instrument_id}?${params.toString()}`,
  );
}

export async function createBacktestJob(
  payload: Record<string, string>,
): Promise<BacktestJobStatus> {
  return apiFetch<BacktestJobStatus>("/api/backtest-jobs", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function fetchBacktestJob(
  jobId: string,
): Promise<BacktestJobStatus> {
  return apiFetch<BacktestJobStatus>(`/api/backtest-jobs/${jobId}`);
}

export async function runBacktestJob(
  jobId: string,
): Promise<BacktestRunResponse> {
  return apiFetch<BacktestRunResponse>(`/api/backtest-jobs/${jobId}/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  });
}

export async function cancelBacktestJob(
  jobId: string,
): Promise<BacktestJobStatus> {
  return apiFetch<BacktestJobStatus>(`/api/backtest-jobs/${jobId}/cancel`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  });
}

export async function fetchBacktestJobEvents(
  jobId: string,
): Promise<BacktestJobEvents> {
  return apiFetch<BacktestJobEvents>(`/api/backtest-jobs/${jobId}/events`);
}

export async function fetchResultSummary(
  resultId: string,
): Promise<ResultDashboardPayload> {
  return apiFetch<ResultDashboardPayload>(`/api/results/${resultId}`);
}

export async function fetchResultArtifacts(
  resultId: string,
): Promise<Record<string, unknown>> {
  return (await fetchResultSummary(resultId)).artifacts;
}

export async function fetchResultTrades(resultId: string): Promise<unknown[]> {
  return (await fetchResultSummary(resultId)).trades;
}

export async function fetchResultFills(resultId: string): Promise<unknown[]> {
  return (await fetchResultSummary(resultId)).fills;
}


export async function fetchLlmConfig(): Promise<LlmConfig> {
  return apiFetch<LlmConfig>("/api/config/llm");
}

export async function saveLlmConfig(
  payload: LlmConfigSavePayload,
): Promise<LlmConfig> {
  return apiFetch<LlmConfig>("/api/config/llm", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function generateAiDraft(
  payload: AiDraftPayload,
): Promise<AiDraftResult> {
  return apiFetch<AiDraftResult>("/api/ai-builder/draft", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function applyAiDraftToBuilder(
  payload: AiDraftPayload,
): Promise<AiDraftApplication> {
  return apiFetch<AiDraftApplication>("/api/ai-builder/apply", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function requestShadowPromotion(payload: {
  strategy_version_id: string;
  result_id: string;
  target: "shadow" | "signal-preview";
}): Promise<PromotionRequestResult> {
  return apiFetch<PromotionRequestResult>("/api/promotions/request", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function validateBacktestProfile(
  profile: Record<string, string>,
): Promise<BacktestProfileValidation> {
  return apiFetch<BacktestProfileValidation>(
    "/api/backtest-profiles/validate",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(profile),
    },
  );
}

export async function approveStrategy(
  strategyId: string,
): Promise<StrategyRecord> {
  return apiFetch<StrategyRecord>(`/api/strategies/${strategyId}/approve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  });
}

export async function cloneStrategy(
  strategyId: string,
): Promise<StrategyRecord> {
  return apiFetch<StrategyRecord>(`/api/strategies/${strategyId}/clone`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  });
}
