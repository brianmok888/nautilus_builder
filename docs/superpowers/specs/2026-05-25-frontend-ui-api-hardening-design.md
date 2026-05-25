# Frontend UI/API Hardening Design

## Goal
Make the staged Nautilus Builder web UI usable enough for VM demos by fixing API JSON failure handling and adding a no-dependency visual shell, while preserving Builder's authoring/observational-only authority boundary.

## Context
The current frontend is a minimal Next.js shell. `apps/web/app/layout.tsx` does not import global CSS, `apps/web/app/page.tsx` uses raw semantic markup, and `apps/web/lib/api.ts` unconditionally parses every response as JSON. On a remote VM this can look like plain text and can surface `JSON.parse` when the frontend receives HTML, text, or an empty/proxy error response.

## Approach
Recommended approach: keep dependencies unchanged and add a small global design system in `apps/web/app/globals.css`, imported by the root layout. Use semantic class names on the existing shell and key components so current markup renders as a dashboard with cards, panels, status badges, terminal styling, and accessible forms. Harden `apiFetch()` by parsing response bodies by content type, tolerating empty bodies, wrapping network failures, and returning clear API/proxy error messages including status, URL, and a text snippet for non-JSON responses.

Rejected alternatives:
- Add Tailwind or a component library: unnecessary for this scaffold and increases install/deploy risk.
- Build a full interactive visual builder: beyond this fix; the current goal is VM usability and clearer API diagnostics.
- Move runtime truth into the UI: violates Builder's boundary; backend remains authoritative.

## Architecture
- `apps/web/lib/api.ts` remains the single frontend API boundary. `ApiError` carries HTTP status, parsed payload if available, URL, and response content type.
- `apps/web/app/globals.css` owns design tokens and shared utility/component classes; no CSS framework is introduced.
- Route pages and operator components receive class names only where needed for visual structure. Text continues to say draft/advisory/observational-only.
- Tests lock API error behavior, global CSS import, no live authority strings, and the presence of styled shell tokens.

## Data and error flow
1. UI calls typed helpers in `apps/web/lib/api.ts`.
2. `apiFetch()` resolves `apiUrl(path)`, performs `fetch`, and reads raw text once.
3. JSON content is parsed only when the response content type indicates JSON and the body is non-empty.
4. Non-OK responses throw `ApiError` with a diagnostic message. Non-JSON responses name likely API/proxy misconfiguration.
5. Network failures throw `ApiError` with status `0` and an API reachability hint.

## Testing
- Add Vitest tests for JSON success, non-JSON HTTP failure, empty non-OK failure, and network failure.
- Add Python source-contract tests for global CSS import and VM-demo shell styling tokens.
- Run frontend typecheck, Vitest, and Next build.
- Run focused Python web tests and broader integration where practical.

## Authority boundary
The UI remains Builder-only. No component may introduce `submit_order`, `TradeAction`, direct shell access, or live trading authority. Promotion and AI surfaces remain advisory/manual-approval only.
