# Nautilus Builder Real Frontend Behavior Design

Date: 2026-05-23

## Summary

The previous frontend operator MVP work created a useful contract scaffold, but review showed it is not a real operator frontend. Pages import API functions without invoking them, components render static text or function names, browser E2E is not executed against a composed runtime, and the implementation plan remains unchecked. This design defines the follow-up pass that converts those stubs into real frontend behavior.

The goal is not to broaden scope. The goal is to make the existing FE-00 through FE-09 surfaces truthful: real data fetching, real forms/state, real API status semantics, real job/event behavior, real typecheck/build evidence, real browser E2E, and reconciled plan checkboxes.

## Recommended approach

Use vertical real-flow slices. Each slice replaces static frontend placeholders with actual behavior and fixes only the backend truth required for that slice.

Rejected alternatives:

- Patch current stubs only: fastest, but keeps fake backend behavior and false readiness.
- Backend truth first only: improves foundations, but delays operator-visible behavior too long.

## Hard boundaries

- Browser frontend uses HTTP/JSON and SSE through Next rewrites; not MCP.
- Frontend never owns backend runtime lifetime.
- Frontend never submits live orders, creates `TradeAction`, reads credentials, or mutates Nautilus-Daedalus.
- Strategy params originate from backend `StrategySpec` contracts and backend validation.
- AI remains advisory; apply actions create draft/frontend state and backend audit records only.
- Redis streams stay Builder-owned (`builder:*`) and do not write `nd:*`.
- Postgres/DB payloads must preserve stable IDs, not display names.

## Architecture changes

### 1. API route parity and status preservation

Current risk: `services/api/app.py` and `services/api/fastapi_app.py` duplicate routes, and FastAPI can drop `ApiResponse.status_code` by returning only JSON.

Design:

- Introduce a shared route registration layer or route table consumed by both the lightweight `ApiApp` and FastAPI bootstrap.
- FastAPI adapters must convert `ApiResponse(status_code=...)` into actual HTTP status responses.
- Tests must assert status parity between `create_app()` and `create_fastapi_app()` for create, missing, validation-error, and success cases.

### 2. Real frontend behavior standard

Every frontend route/component converted in this pass must include:

- actual API call or form submit handler;
- loading state;
- error state;
- empty/success state;
- rendered response data;
- no placeholder assertions based only on imported function names.

Client components should be used where interaction is required. Server components may fetch initial read-only data when appropriate.

### 3. Testing standard

Replace string-only frontend evidence with behavior-oriented tests:

- TypeScript unit tests for pure helpers such as terminal parser, graph/spec conversion, and API error handling.
- Component tests for forms, loading/error/success states, and user actions.
- Python API tests for backend status/payload contracts.
- Playwright E2E against a composed Next + FastAPI local runtime.

Text/file-presence tests may remain as smoke checks, but they cannot be the primary evidence for real frontend readiness.

## Slice design

### Slice 1: build/typecheck and API parity baseline

Purpose: establish that the frontend can actually build and that frontend API behavior matches real FastAPI, not only the in-process test router.

Work:

- Make `npm install`, `npm run typecheck`, and `npm run build` executable in `apps/web`.
- Fix package lock correctness.
- Add FastAPI status-code parity tests.
- Add route table/shared registration or equivalent parity guard.
- Add CORS/rewrite documentation for local dev.

Acceptance:

- `npm run typecheck` passes.
- `npm run build` passes.
- Python full suite passes.
- FastAPI and `ApiApp` route status behavior match.

### Slice 2: Strategy CRUD real UI

Purpose: replace strategy list/detail placeholders with rendered backend data and create/update/version actions.

Work:

- Strategies page fetches and renders strategy rows.
- Empty, loading, and error states exist.
- Create strategy form submits to backend.
- Detail page fetches strategy detail and displays lineage/version history.
- Save draft and create version actions call backend and re-render response.

Acceptance:

- Component tests prove data is rendered from mocked API responses.
- API tests prove stable `strategy_lineage_id` and `strategy_version_id` behavior.
- No display name is used as identity.

### Slice 3: Builder graph/spec real state

Purpose: make the builder an interactive stateful editor rather than static labels.

Work:

- Add reducer/store for graph nodes, edges, selected block, spec preview, dirty state, and validation messages.
- Block palette adds supported nodes.
- Inspector edits node params.
- Graph/spec conversion updates preview.
- Backend validation is invoked before save/version/backtest.

Acceptance:

- Tests exercise add/edit/select/serialize/validate flows.
- Unsupported params/operators are rejected before or by backend validation.

### Slice 4: Market profile real form

Purpose: make adapter/instrument/timeframe/date range selection real.

Work:

- Fetch adapters.
- Search instruments based on selected adapter.
- Fetch/display data availability.
- Submit profile validation.
- Render validation errors and success response with stable profile identity.

Acceptance:

- Tests exercise user selection and validation calls.
- Frontend route shape is stable even if backend route internals differ.

### Slice 5: Backtest job and event observation

Purpose: create backend-owned jobs and observe real backend state.

Work:

- Backtest job creation returns actual job ID from backend service.
- Job detail route fetches real status.
- Cancel route calls service state transition.
- Events endpoint returns typed replay data.
- Add SSE endpoint or client-side event subscription over the runtime stream seam.
- Terminal commands call status/log/cancel APIs or render typed responses.

Acceptance:

- Tests prove create/status/cancel operate on same job ID.
- Events are typed and replayable.
- Terminal forbidden commands cannot execute shell/network/secret access.

### Slice 6: Results dashboard real rendering

Purpose: render actual result payload data instead of tab labels only.

Work:

- Fetch result summary.
- Render metrics, artifacts, trades, fills, logs.
- Add empty states for missing data.
- Preserve no-execution controls.

Acceptance:

- Tests assert displayed values come from mocked/backend payloads.
- No live execution controls appear.

### Slice 7: Advisory AI real flow

Purpose: turn AI copilot into an input/draft/apply/audit flow.

Work:

- Prompt form submits to AI draft route.
- Show explanation, validation errors, and draft spec.
- Apply-to-builder updates builder draft only after validation.
- Preserve `ai_thread_id`, `improvement_cycle_id`, `strategy_lineage_id`, and `strategy_version_id`.

Acceptance:

- Tests prove invalid/forbidden AI output cannot be applied.
- Audit record retains lane and lineage IDs.

### Slice 8: Safe promotion real flow

Purpose: make promotion request a real form/action while preserving shadow/signal-preview only.

Work:

- Promotion panel receives strategy version/result context.
- Request submits to backend.
- Render manual approval state.
- Reject live targets in UI and backend.

Acceptance:

- Tests prove live target rejected.
- Tests prove stable IDs sent, not display labels.

### Slice 9: composed browser E2E and plan reconciliation

Purpose: prove the real frontend behavior, not string scaffolds.

Work:

- Start FastAPI and Next in Playwright `webServer` setup or equivalent script.
- Run a browser path covering strategy creation, profile validation, job creation, event observation, result view, AI draft/apply, and promotion request.
- Update verification report with actual commands and outcomes.
- Reconcile plan checkboxes: mark only truly completed steps.

Acceptance:

- Playwright E2E passes in local environment or records a specific external blocker.
- Full Python suite passes.
- Frontend typecheck/build passes.
- Plan file accurately reflects execution truth.

## Data flow

```text
User action
  -> client component state/form
  -> typed API client
  -> Next rewrite /api/*
  -> FastAPI route with correct status code
  -> package service/repository
  -> stable payload IDs
  -> UI re-renders loading/error/success/data state
```

Long-running work:

```text
Create BacktestJob
  -> backend job_id
  -> worker/service updates backend state
  -> runtime events published/replayed from builder:* stream
  -> UI observes via SSE/replay
```

## Error handling

- API client raises typed `ApiError` with status and payload.
- Components render validation errors from backend response payloads.
- Network/runtime errors show retryable error states.
- Missing resources display not-found states from actual 404s.
- Forbidden actions display explicit hardguard messages.

## Spec self-review

- No placeholder TODO/TBD markers remain.
- Scope is focused on converting existing FE scaffold into real behavior.
- The design does not introduce MCP or live execution authority.
- Backend changes are limited to what real frontend behavior requires.
- Testing requirements explicitly reject string-only proof as completion evidence.
