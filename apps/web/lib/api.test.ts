import { afterEach, describe, expect, it, vi } from "vitest";
import { ApiError, apiFetch, runBacktestJob, startExecutionLanePaperSession, stopExecutionLaneSession } from "./api";

describe("apiFetch", () => {
  afterEach(() => vi.restoreAllMocks());

  it("returns parsed JSON for successful backend responses", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => Response.json({ ok: true, service: "builder" })),
    );

    await expect(
      apiFetch<{ ok: boolean }>("/health/backend"),
    ).resolves.toMatchObject({ ok: true });
  });

  it("throws a clear API/proxy error when an HTTP response is not JSON", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(
        async () =>
          new Response("<html>proxy error</html>", {
            status: 502,
            headers: { "Content-Type": "text/html" },
          }),
      ),
    );

    await expect(apiFetch("/api/strategies")).rejects.toMatchObject({
      name: "ApiError",
      status: 502,
      url: "/api/strategies",
      contentType: "text/html",
      payload: { body: "<html>proxy error</html>" },
    });
    await expect(apiFetch("/api/strategies")).rejects.toThrow(
      /expected JSON but received text\/html/i,
    );
  });

  it("describes empty backend error responses without JSON.parse noise", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => new Response("", { status: 504 })),
    );

    await expect(apiFetch("/api/backtest-jobs")).rejects.toThrow(
      /empty response body/i,
    );
  });

  it("preserves JSON error payloads without calling them empty", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        Response.json(
          { detail: "requested data type unsupported" },
          { status: 422 },
        ),
      ),
    );

    await expect(
      apiFetch("/api/backtest-profiles/validate"),
    ).rejects.toMatchObject({
      status: 422,
      payload: { detail: "requested data type unsupported" },
    });
    await expect(
      apiFetch("/api/backtest-profiles/validate"),
    ).rejects.not.toThrow(/empty response body/i);
  });



  it("posts to the backend-owned BacktestNode run route", async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      expect(String(input)).toBe("/api/backtest-jobs/bt_backtest_001/run");
      expect(init?.method).toBe("POST");
      expect(String(init?.body)).toBe("{}");
      return Response.json({
        mode: "backend_owned_backtestnode",
        job: { job_id: "bt_backtest_001", status: "succeeded", stage: "SUCCEEDED" },
        result: { engine_mode: "strategy_spec_catalog_replay", orders: 0 },
        events: [{ stage: "RUNNING" }, { stage: "SUCCEEDED" }],
      });
    });
    vi.stubGlobal("fetch", fetchMock);

    await expect(runBacktestJob("bt_backtest_001")).resolves.toMatchObject({
      mode: "backend_owned_backtestnode",
      job: { status: "succeeded" },
      result: { engine_mode: "strategy_spec_catalog_replay" },
      events: [{ stage: "RUNNING" }, { stage: "SUCCEEDED" }],
    });
  });

  it("attaches configured local bearer token to API requests when no Authorization header is provided", async () => {
    const fetchMock = vi.fn(async () => Response.json({ ok: true }));
    vi.stubGlobal("fetch", fetchMock);
    vi.stubEnv("NEXT_PUBLIC_BUILDER_API_TOKEN", "nb_local_dev_token");

    await apiFetch<{ ok: boolean }>("/api/strategies");

    const calls = fetchMock.mock.calls as unknown as [string, RequestInit][];
    const init = calls[0][1];
    expect(new Headers(init.headers).get("Authorization")).toBe(
      "Bearer nb_local_dev_token",
    );
  });

  it("does not override an explicit Authorization header", async () => {
    const fetchMock = vi.fn(async () => Response.json({ ok: true }));
    vi.stubGlobal("fetch", fetchMock);
    vi.stubEnv("NEXT_PUBLIC_BUILDER_API_TOKEN", "nb_local_dev_token");

    await apiFetch<{ ok: boolean }>("/api/strategies", {
      headers: { Authorization: "Bearer caller_token" },
    });

    const calls = fetchMock.mock.calls as unknown as [string, RequestInit][];
    const init = calls[0][1];
    expect(new Headers(init.headers).get("Authorization")).toBe(
      "Bearer caller_token",
    );
  });

  it("surfaces FastAPI bearer-auth errors with action guidance", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        Response.json(
          { error: "auth_required", details: "Bearer token is required" },
          { status: 401 },
        ),
      ),
    );

    await expect(apiFetch("/api/strategies")).rejects.toThrow(
      /configure BUILDER_API_TOKEN or NEXT_PUBLIC_BUILDER_API_TOKEN/i,
    );
  });

  it("wraps network failures with API base URL guidance", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => {
        throw new TypeError("fetch failed");
      }),
    );

    await expect(apiFetch("/health/backend")).rejects.toMatchObject({
      status: 0,
      url: "/health/backend",
      payload: { cause: "fetch failed" },
    });
    await expect(apiFetch("/health/backend")).rejects.toThrow(
      /unable to reach Nautilus Builder API/i,
    );
  });
  it("posts credential-slot bootstrap payload without echoing secrets", async () => {
    const { saveExecutionLaneCredentialSlot } = await import("./api");
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      expect(String(input)).toBe("/api/execution-lane/credential-slots");
      expect(init?.method).toBe("POST");
      const payload = JSON.parse(String(init?.body));
      expect(payload).toMatchObject({
        runtime_profile_id: "rp_paper_tradingnode",
        venue: "BINANCE",
        credential_values: { BINANCE_API_KEY: "test-binance-key" },
      });
      return Response.json(
        {
          credential_slot_ref: "credslot://local-env/project_alpha/rp_paper_tradingnode/binance",
          tenant_id: "tenant_a",
          project_id: "project_alpha",
          runtime_profile_id: "rp_paper_tradingnode",
          adapter_id: "BINANCE_PERP",
          venue: "BINANCE",
          lane_mode: "paper",
          secrets_storage: "local_env_file",
          env_file_path: ".env.execution.local",
          redacted_keys: ["BINANCE_API_KEY"],
          fingerprint: "a".repeat(64),
          browser_secret_echo: false,
        },
        { status: 201 },
      );
    });
    vi.stubGlobal("fetch", fetchMock);

    await expect(
      saveExecutionLaneCredentialSlot({
        tenant_id: "tenant_a",
        project_id: "project_alpha",
        runtime_profile_id: "rp_paper_tradingnode",
        adapter_id: "BINANCE_PERP",
        venue: "BINANCE",
        lane_mode: "paper",
        requested_by: "ops_user",
        credential_values: { BINANCE_API_KEY: "test-binance-key" },
      }),
    ).resolves.toMatchObject({
      credential_slot_ref: "credslot://local-env/project_alpha/rp_paper_tradingnode/binance",
      browser_secret_echo: false,
      redacted_keys: ["BINANCE_API_KEY"],
    });
  });


  it("posts paper TradingNode session start and stop through backend-owned routes", async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      const payload = JSON.parse(String(init?.body));
      if (url === "/api/execution-lane/sessions/start") {
        expect(init?.method).toBe("POST");
        expect(payload).toEqual({
          runtime_profile_id: "rp_paper_tradingnode",
          command_id: "exec_cmd_paper_001",
          worker_id: "web_execution_worker",
          project_id: "project_alpha",
        });
        return Response.json({
          session_id: "exec_session_001",
          command_id: "exec_cmd_paper_001",
          runtime_profile_id: "rp_paper_tradingnode",
          tenant_id: "tenant_a",
          project_id: "project_alpha",
          lane_mode: "paper",
          adapter_id: "BINANCE_PERP",
          venue: "BINANCE",
          status: "RUNNING",
          lifecycle_status: "RUNNING",
          runner_mode: "contract_dry_run",
          worker_id: "web_execution_worker",
          started_at: "2026-05-27T00:00:00Z",
          runtime_environment: "sandbox",
          node_runtime: "python_trading_node",
          runtime_label: "python_live_integration_specific",
          future_runtime: "rust_live_node",
          strategy_lineage_id: "lineage_ema_rsi",
          strategy_version_id: "strategy_001_v004",
          trade_action_id: "ta_paper_001",
          credential_slot_ref: "credslot://local-env/project_alpha/rp_paper_tradingnode/binance",
          credential_env_keys: ["BINANCE_API_KEY", "BINANCE_API_SECRET"],
          credential_values_resolved: true,
          tradingnode_config: { config_type: "TradingNodeConfig" },
          attached_strategy: { strategy_version_id: "strategy_001_v004", may_submit_order: false },
          lifecycle_events: [{ status: "RUNNING", message: "started", timestamp: "2026-05-27T00:00:00Z", session_id: "exec_session_001" }],
          browser_credentials_allowed: false,
          credential_inputs_allowed: false,
          strategy_lane_coupled: false,
          live_trading_enabled: false,
          execution_authority: false,
          may_submit_order: false,
        }, { status: 202 });
      }
      expect(url).toBe("/api/execution-lane/sessions/exec_session_001/stop");
      expect(init?.method).toBe("POST");
      expect(payload).toEqual({ worker_id: "web_execution_worker" });
      return Response.json({
        session_id: "exec_session_001",
        command_id: "exec_cmd_paper_001",
        runtime_profile_id: "rp_paper_tradingnode",
        tenant_id: "tenant_a",
        project_id: "project_alpha",
        lane_mode: "paper",
        adapter_id: "BINANCE_PERP",
        venue: "BINANCE",
        status: "DISPOSED",
        lifecycle_status: "DISPOSED",
        runner_mode: "contract_dry_run",
        worker_id: "web_execution_worker",
        started_at: "2026-05-27T00:00:00Z",
        stopped_at: "2026-05-27T00:01:00Z",
        disposed_at: "2026-05-27T00:01:00Z",
        runtime_environment: "sandbox",
        node_runtime: "python_trading_node",
        runtime_label: "python_live_integration_specific",
        future_runtime: "rust_live_node",
        strategy_lineage_id: "lineage_ema_rsi",
        strategy_version_id: "strategy_001_v004",
        trade_action_id: "ta_paper_001",
        credential_slot_ref: "credslot://local-env/project_alpha/rp_paper_tradingnode/binance",
        credential_env_keys: ["BINANCE_API_KEY", "BINANCE_API_SECRET"],
        credential_values_resolved: true,
        tradingnode_config: { config_type: "TradingNodeConfig" },
        attached_strategy: { strategy_version_id: "strategy_001_v004", may_submit_order: false },
        lifecycle_events: [{ status: "DISPOSED", message: "disposed", timestamp: "2026-05-27T00:01:00Z", session_id: "exec_session_001" }],
        browser_credentials_allowed: false,
        credential_inputs_allowed: false,
        strategy_lane_coupled: false,
        live_trading_enabled: false,
        execution_authority: false,
        may_submit_order: false,
      }, { status: 202 });
    });
    vi.stubGlobal("fetch", fetchMock);

    const started = await startExecutionLanePaperSession({
      runtime_profile_id: "rp_paper_tradingnode",
      command_id: "exec_cmd_paper_001",
      worker_id: "web_execution_worker",
      project_id: "project_alpha",
    });
    expect(started.lifecycle_status).toBe("RUNNING");
    expect(started.tradingnode_config.config_type).toBe("TradingNodeConfig");
    await expect(stopExecutionLaneSession("exec_session_001", { worker_id: "web_execution_worker" })).resolves.toMatchObject({
      lifecycle_status: "DISPOSED",
    });
  });

});
