import { afterEach, describe, expect, it, vi } from "vitest";
import { ApiError, apiFetch } from "./api";

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
});
