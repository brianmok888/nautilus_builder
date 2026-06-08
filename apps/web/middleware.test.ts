import { afterEach, describe, expect, it, vi } from "vitest";
import {
  apiProxyDestination,
  headersWithServerAuth,
} from "./middleware";

describe("middleware API proxy auth", () => {
  afterEach(() => vi.unstubAllEnvs());

  it("maps API requests to the server-side Builder API base URL", () => {
    vi.stubEnv("BUILDER_API_BASE_URL", "http://api:8000");

    const destination = apiProxyDestination(
      new URL("http://web.local/api/strategies?limit=10"),
    );

    expect(destination?.toString()).toBe(
      "http://api:8000/api/strategies?limit=10",
    );
  });

  it("does not proxy non-API requests", () => {
    vi.stubEnv("BUILDER_API_BASE_URL", "http://api:8000");

    const destination = apiProxyDestination(new URL("http://web.local/config"));

    expect(destination).toBeNull();
  });

  it("ignores public API base URLs for the server-side token proxy", () => {
    vi.stubEnv("NEXT_PUBLIC_API_BASE_URL", "https://public-api.example.com");

    const destination = apiProxyDestination(
      new URL("http://web.local/api/strategies"),
    );

    expect(destination?.toString()).toBe(
      "http://127.0.0.1:8000/api/strategies",
    );
  });

  it("injects the server-side Builder API token without using a public token", () => {
    vi.stubEnv("BUILDER_ENV", "local");
    vi.stubEnv("BUILDER_API_TOKEN", "nb_server_only_token");
    vi.stubEnv("NEXT_PUBLIC_BUILDER_API_TOKEN", "nb_public_token");

    const headers = headersWithServerAuth(new Headers());

    expect(headers.get("Authorization")).toBe("Bearer nb_server_only_token");
  });

  it("does not override caller-provided Authorization headers", () => {
    vi.stubEnv("BUILDER_ENV", "local");
    vi.stubEnv("BUILDER_API_TOKEN", "nb_server_only_token");
    const incoming = new Headers({ Authorization: "Bearer caller_token" });

    const headers = headersWithServerAuth(incoming);

    expect(headers.get("Authorization")).toBe("Bearer caller_token");
  });

  it("does not inject the server token outside local mode", () => {
    vi.stubEnv("BUILDER_ENV", "production");
    vi.stubEnv("BUILDER_API_TOKEN", "nb_server_only_token");

    const headers = headersWithServerAuth(new Headers());

    expect(headers.get("Authorization")).toBeNull();
  });
});
