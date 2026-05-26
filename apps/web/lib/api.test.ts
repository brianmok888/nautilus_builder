import { afterEach, describe, expect, it, vi } from "vitest";
import { ApiError, apiFetch, runBacktestJob } from "./api";

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

});
