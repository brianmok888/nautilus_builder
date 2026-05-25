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
