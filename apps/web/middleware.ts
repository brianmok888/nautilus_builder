import { NextResponse, type NextRequest } from "next/server";

const HTML_NO_STORE = "no-store, max-age=0, must-revalidate";

export function middleware(_request: NextRequest) {
  const response = NextResponse.next();

  // VM demos frequently restart/rebuild the Next app in place. Do not let stale
  // prerendered HTML point browsers at removed `_next/static` chunk hashes.
  // Static assets keep Next's immutable caching; app/API HTML gets no-store.
  response.headers.set("Cache-Control", HTML_NO_STORE);
  response.headers.set("Pragma", "no-cache");
  response.headers.set("Expires", "0");

  return response;
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
