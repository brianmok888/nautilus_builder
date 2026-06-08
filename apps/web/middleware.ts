import { NextResponse, type NextRequest } from "next/server";

const HTML_NO_STORE = "no-store, max-age=0, must-revalidate";
const DEFAULT_SERVER_API_BASE_URL = "http://127.0.0.1:8000";
const API_PREFIX = "/api/";

function withNoStore(response: NextResponse): NextResponse {
  // VM demos frequently restart/rebuild the Next app in place. Do not let stale
  // prerendered HTML point browsers at removed `_next/static` chunk hashes.
  // Static assets keep Next's immutable caching; app/API HTML gets no-store.
  response.headers.set("Cache-Control", HTML_NO_STORE);
  response.headers.set("Pragma", "no-cache");
  response.headers.set("Expires", "0");

  return response;
}

function serverApiBaseUrl(): string {
  return (
    process.env.BUILDER_API_BASE_URL ??
    DEFAULT_SERVER_API_BASE_URL
  ).trim();
}

function serverApiToken(): string {
  return (process.env.BUILDER_API_TOKEN ?? "").trim();
}

function serverTokenProxyAllowed(): boolean {
  const configuredEnvironments = [
    process.env.BUILDER_ENV ?? "",
    process.env.APP_ENV ?? "",
  ]
    .map((value) => value.trim().toLowerCase())
    .filter((value) => value.length > 0);
  return (
    configuredEnvironments.length === 0 ||
    configuredEnvironments.every((value) => value === "local")
  );
}

export function apiProxyDestination(requestUrl: URL): URL | null {
  if (!requestUrl.pathname.startsWith(API_PREFIX)) return null;
  return new URL(`${requestUrl.pathname}${requestUrl.search}`, serverApiBaseUrl());
}

export function headersWithServerAuth(headers: Headers): Headers {
  const nextHeaders = new Headers(headers);
  const token = serverApiToken();
  if (token && serverTokenProxyAllowed() && !nextHeaders.has("Authorization")) {
    nextHeaders.set("Authorization", `Bearer ${token}`);
  }
  return nextHeaders;
}

export function middleware(request: NextRequest) {
  const destination = apiProxyDestination(request.nextUrl);
  if (destination !== null && serverApiToken() && serverTokenProxyAllowed()) {
    return withNoStore(
      NextResponse.rewrite(destination, {
        request: { headers: headersWithServerAuth(request.headers) },
      }),
    );
  }

  return withNoStore(NextResponse.next());
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
