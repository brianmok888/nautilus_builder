# Frontend-Ready Operator MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax intentionally. Follow TDD: write/confirm failing tests first, implement minimal code, verify, then commit before moving to the next milestone.

## Source design

- Design spec: `docs/superpowers/specs/2026-05-23-frontend-ready-operator-mvp-design.md`
- Source truth docs: `doc/nautilus_builder_spec.md`, `doc/nautilus_builder_hardguards.md`
- Current enforced contracts: `tests/`, especially `tests/workflow_spine`, `tests/backtest_runner`, `tests/api`, `tests/web`, `tests/integration`

## Critical alignment notes for ND, NT, AI lane params, DB, and Redis

This plan is frontend-focused, but it must not create drift from NautilusTrader (NT), Nautilus-Daedalus (ND), AI lineage, Postgres, or Redis event truth.

### Current alignment evidence

- ND boundary is Builder-side advisory only in `packages/workflow_spine/nd_compat.py`.
- ND advisory tests preserve stable IDs in `tests/workflow_spine/test_nd_ai_compatibility.py`.
- Builder may publish to `builder:nd:advisory`; it must not write ND-owned streams such as `nd:*`.
- NT integration is currently a boundary seam in `packages/backtest_runner/nautilus_engine.py`; real engine execution remains downstream.
- StrategySpec is the canonical strategy param model in `packages/strategy_spec/models.py`.
- Postgres runtime config exists in `packages/workflow_spine/postgres_runtime.py`.
- Builder-owned Postgres schema starts in `infra/migrations/001_builder_workflow_storage.sql`.
- Redis runtime stream namespace is Builder-owned in `packages/runtime_events/redis_stream.py` and uses `builder:runtime:{job_id}`.

### Mandatory anti-drift rules

- Frontend must never invent strategy params outside `StrategySpec` schema.
- Frontend builder graph state must roundtrip through backend StrategySpec validation before save/version/backtest.
- AI lane params must carry `ai_thread_id`, `improvement_cycle_id`, `strategy_lineage_id`, and `strategy_version_id` when they influence workflow events or suggestions.
- Postgres tables must store stable IDs and payload schemas; do not use display names as identity.
- Redis stream names must stay Builder-owned (`builder:*`) and must not write `nd:*`.
- NT backtest config must be built from validated StrategySpec version + adapter/instrument profile + compile/validation artifacts, not from ad hoc frontend state.
- ND promotion/advisory payloads must be derived from stored backend state and stable IDs, never from unsaved browser state.

## File map

### Frontend infrastructure

- `apps/web/package.json` — scripts and dependencies.
- `apps/web/package-lock.json` or chosen lockfile — reproducible frontend install.
- `apps/web/tsconfig.json` — TypeScript config.
- `apps/web/next.config.*` — proxy/rewrite or API base configuration.
- `apps/web/lib/api.ts` — typed API client.
- `apps/web/lib/types.ts` — generated or hand-maintained frontend DTOs mirrored from backend contracts.
- `apps/web/lib/query.ts` — query client setup if TanStack Query is added.
- `apps/web/app/layout.tsx`, `apps/web/app/page.tsx` — shell and landing route.

### Strategy and builder UI

- `apps/web/app/strategies/page.tsx` — strategies list.
- `apps/web/app/strategies/[strategyId]/page.tsx` — strategy detail/version route.
- `apps/web/app/builder/[strategyId]/page.tsx` — builder workspace route.
- `apps/web/components/strategy-builder/*` — graph, palette, inspector, spec editor, validation panel.
- `apps/web/lib/strategySpec.ts` — graph/spec conversion and schema helpers.

### Backtest/profile/results UI

- `apps/web/components/market/*` — adapter/instrument/profile selectors.
- `apps/web/app/backtests/[jobId]/page.tsx` — job status and terminal route.
- `apps/web/components/terminal/*` — observational command parser and log/event display.
- `apps/web/app/results/[resultId]/page.tsx` — result dashboard route.
- `apps/web/components/results/*` — metrics, equity, trades, fills, logs, artifacts.

### AI and promotion UI

- `apps/web/components/ai-builder/*` — prompt, draft, audit/thread, apply-to-builder surfaces.
- `apps/web/components/promotions/*` — safe promotion request UI.

### Backend/API seams that frontend will require

- `services/api/fastapi_app.py` — real mounted route surface.
- `services/api/routes/strategies.py` — StrategySpec CRUD/version payload helpers.
- `services/api/routes/market_catalog.py` — adapter/instrument/profile validation routes.
- `services/api/routes/backtest_jobs.py` — create/status/cancel jobs.
- `services/api/routes/runtime_events.py` — replay/SSE event routes.
- `services/api/routes/workflow_results.py` — result/projection routes.
- `services/api/routes/ai_builder.py` — advisory AI route.
- `services/api/routes/promotions.py` — safe shadow/signal-preview promotion route.

### Anti-drift backend contracts

- `packages/strategy_spec/models.py` — canonical strategy params.
- `packages/strategy_validation/validators.py` — hard validation.
- `packages/backtest_runner/config_builder.py` — NT-safe config build.
- `packages/backtest_runner/nautilus_engine.py` — NT engine boundary.
- `packages/workflow_spine/models.py` — stable workflow IDs.
- `packages/workflow_spine/nd_compat.py` — ND advisory mapping.
- `packages/workflow_spine/postgres_runtime.py` — Postgres connection seam.
- `packages/runtime_events/redis_stream.py` — Redis stream seam.
- `infra/migrations/*` — Builder-owned DB schema.

## FE-00: Alignment guard baseline before frontend work

Goal: prevent frontend implementation from drifting away from ND/NT/DB/Redis truth.

- [ ] Write failing tests in `tests/integration/test_frontend_alignment_guards.py` asserting the design/plan require StrategySpec as the source of strategy params, stable workflow IDs for AI/ND, Builder-owned Postgres schema, and Builder-owned Redis streams.
- [ ] Run `rtk pytest tests/integration/test_frontend_alignment_guards.py` and confirm RED.
- [ ] Add minimal docs/contract helper references if needed so the test can verify those guardrails without duplicating implementation.
- [ ] Run `rtk pytest tests/integration/test_frontend_alignment_guards.py` and confirm GREEN.
- [ ] Run `rtk pytest tests/workflow_spine tests/backtest_runner tests/runtime_events tests/api`.
- [ ] Commit: `guard frontend alignment contracts`.

## FE-01: Frontend infrastructure and typed API client

Goal: make the frontend buildable, typed, and explicitly connected to backend HTTP/SSE contracts.

- [ ] Write failing tests checking `apps/web` has a lockfile, `tsconfig.json`, API base/proxy config, and typed DTO/client files.
- [ ] Run the frontend infra tests and confirm RED.
- [ ] Add lockfile using the project’s package manager; default to npm if no package manager is already chosen.
- [ ] Add `tsconfig.json` with strict TypeScript settings.
- [ ] Add `next.config.*` with dev rewrite or documented `NEXT_PUBLIC_API_BASE_URL` handling.
- [ ] Replace loose `apps/web/lib/api.ts` responses with typed request/response helpers.
- [ ] Add response error handling that preserves backend validation messages.
- [ ] Ensure typed DTOs mirror backend contracts; do not invent fields outside current Python models.
- [ ] Add a backend health client helper.
- [ ] Run frontend infra tests and confirm GREEN.
- [ ] If dependencies are installable in the environment, run `npm install` then `npm run build` under `apps/web`; otherwise document the environment blocker in the commit message/body.
- [ ] Run `rtk pytest tests/web tests/api/test_fastapi_app.py`.
- [ ] Commit: `add typed frontend API foundation`.

## FE-02: Strategy CRUD UX and API versioning

Goal: provide real strategy list/detail/create/update/version flows backed by StrategySpec and stable lineage IDs.

- [ ] Write failing backend tests for StrategySpec update/version routes in `tests/api/test_strategies.py`.
- [ ] Write failing frontend contract tests for strategies list/detail pages and typed API calls.
- [ ] Confirm RED.
- [ ] Extend backend strategy repository/service to preserve `strategy_id`, `strategy_lineage_id`, `strategy_version_id`, `created_from`, stage, status, and payload.
- [ ] Add FastAPI and in-process routes for draft update and version creation.
- [ ] Ensure persisted/versioned strategy params validate against `packages/strategy_spec/models.py`.
- [ ] Implement strategies list and detail pages.
- [ ] Implement create draft and save draft UI state.
- [ ] Display version history and validation status.
- [ ] Add tests proving display names are not used as identity.
- [ ] Run `rtk pytest tests/api/test_strategies.py tests/strategy_spec tests/workflow_spine tests/web`.
- [ ] Commit: `add strategy CRUD frontend flow`.

## FE-03: Interactive Strategy Builder

Goal: replace placeholder Builder with graph/spec editor that roundtrips through canonical StrategySpec.

- [ ] Write failing TypeScript/Python contract tests for graph to StrategySpec conversion and StrategySpec to graph deserialization.
- [ ] Confirm RED.
- [ ] Add graph/spec conversion helpers in `apps/web/lib/strategySpec.ts`.
- [ ] Add block palette using only allowed current StrategySpec primitives unless backend schema expands first.
- [ ] Add canvas component using React Flow or an explicit lightweight graph implementation if dependency install is blocked.
- [ ] Add inspector form for indicator/rule/risk params.
- [ ] Add StrategySpec preview/editor.
- [ ] Route validation through backend; do not validate only in the browser.
- [ ] Add inline validation panel.
- [ ] Add dirty state and save draft action.
- [ ] Add tests proving unsupported params/operators cannot be emitted by the UI.
- [ ] Run `rtk pytest tests/web tests/strategy_spec tests/strategy_validation tests/api` and frontend tests/build if available.
- [ ] Commit: `add interactive strategy builder`.

## FE-04: Market and backtest profile UX

Goal: make adapter/instrument/timeframe/date-range selection real and validated by backend profile contracts.

- [ ] Write failing tests for query-friendly instrument/data availability route compatibility or client wrapper stability.
- [ ] Write failing frontend tests for adapter selector, instrument search, data availability panel, and profile validation response rendering.
- [ ] Confirm RED.
- [ ] Align API route shapes to frontend-friendly query contracts or provide typed client wrappers that hide current path params.
- [ ] Implement adapter selector from backend adapters endpoint.
- [ ] Implement instrument search with adapter dependency.
- [ ] Implement timeframe/date-range/profile form.
- [ ] Implement data availability display.
- [ ] Implement profile validation call and error display.
- [ ] Ensure profile validation output can be stored with `adapter_profile_id`/stable profile refs before job creation.
- [ ] Run `rtk pytest tests/api/test_backtest_profiles.py tests/api/test_market_catalog.py tests/instrument_registry tests/adapter_registry tests/web`.
- [ ] Commit: `add market profile frontend validation`.

## FE-05: Backtest job creation, status, Redis/SSE events, and terminal

Goal: operators can create backend-owned jobs and observe them through durable status/events.

- [ ] Write failing backend tests for `POST /api/backtest-jobs`, `GET /api/backtest-jobs/{job_id}`, and `POST /api/backtest-jobs/{job_id}/cancel`.
- [ ] Write failing SSE/replay tests asserting Redis stream names remain `builder:*` and support reconnect replay.
- [ ] Write failing terminal command parser tests for allowed/forbidden commands.
- [ ] Confirm RED.
- [ ] Add/extend backtest job API routes over existing `packages/backtest_jobs` service.
- [ ] Ensure job creation requires saved StrategySpec version, validated profile, validation report, and compile artifact refs.
- [ ] Add cancellation request route that mutates backend job state only.
- [ ] Implement SSE endpoint over runtime event stream/replay seam.
- [ ] Implement job detail page with status/progress.
- [ ] Implement observational terminal with allowed command parser.
- [ ] Ensure no terminal command can read secrets, run shell commands, or mutate worker memory.
- [ ] Run `rtk pytest tests/backtest_jobs tests/runtime_events tests/backtest_runner tests/api tests/web`.
- [ ] Commit: `add frontend backtest job console`.

## FE-06: Results dashboard

Goal: show backend-computed result data and artifacts without execution authority.

- [ ] Write failing tests for results summary/artifacts/trades/fills/logs API payloads.
- [ ] Write failing frontend tests for result dashboard tabs and no-execution controls.
- [ ] Confirm RED.
- [ ] Extend result API payloads with metrics, equity, trades, fills, logs, and artifact refs.
- [ ] Implement result dashboard route using typed API client.
- [ ] Add summary metrics cards.
- [ ] Add equity chart placeholder or real chart if dependency is approved/available.
- [ ] Add trades/fills/logs/artifacts tabs.
- [ ] Add tests proving no `submit_order`, `TradeAction`, broker credential, or execution controls appear.
- [ ] Run `rtk pytest tests/api tests/backtest_runner tests/web tests/integration` and frontend tests/build if available.
- [ ] Commit: `add results dashboard frontend`.

## FE-07: Advisory AI copilot UX with lane/audit params

Goal: make AI drafting usable while preserving advisory-only and stable AI lane lineage.

- [ ] Write failing backend tests requiring AI audit records to carry `ai_thread_id`, stage, accepted flag, and any related strategy lineage/version IDs when applied.
- [ ] Write failing frontend tests for prompt, draft preview, validation, audit/thread display, and apply-to-builder action.
- [ ] Confirm RED.
- [ ] Extend AI route/client payloads to include `ai_thread_id` and optional `improvement_cycle_id`.
- [ ] Add apply-to-builder action that updates draft UI state only after validation.
- [ ] Ensure applied AI drafts are saved as draft-stage StrategySpec versions before influencing jobs.
- [ ] Ensure ND advisory mapping receives stable IDs only from backend-saved workflow events.
- [ ] Add tests rejecting AI output containing live execution or unsupported params.
- [ ] Run `rtk pytest tests/ai_builder tests/workflow_spine/test_nd_ai_compatibility.py tests/strategy_validation tests/web tests/api`.
- [ ] Commit: `add advisory AI frontend flow`.

## FE-08: Safe promotion request UX

Goal: operators can request shadow/signal-preview promotion without creating live authority.

- [ ] Write failing tests for promotion request UI/API carrying stable StrategySpec version/result IDs and safe target only.
- [ ] Confirm RED.
- [ ] Extend promotion API/client as needed for request status and manual approval state.
- [ ] Implement promotion panel on strategy/result pages.
- [ ] Limit targets to shadow/signal-preview modes.
- [ ] Display validation/backtest/artifact prerequisites.
- [ ] Display manual approval state.
- [ ] Add tests proving live execution controls are absent and forbidden terms are rejected.
- [ ] Run `rtk pytest tests/promotions tests/workflow_spine tests/web tests/api`.
- [ ] Commit: `add safe promotion request frontend`.

## FE-09: Full browser E2E and verification report

Goal: prove the operator MVP path against composed local services where available.

- [ ] Write failing Playwright E2E for create/edit StrategySpec, profile validation, job creation, event observation, result dashboard, AI apply, and promotion request.
- [ ] Confirm RED or document environment blockers if frontend dependencies/services cannot run.
- [ ] Add local stack startup instructions/scripts for Next + FastAPI + backing service seams.
- [ ] Add generated verification report command or script.
- [ ] Make Playwright test run against the local composed stack.
- [ ] Ensure browser refresh/reconnect preserves backend job status via API/replay, not browser state.
- [ ] Generate verification report under `docs/verification/`.
- [ ] Run full Python suite: `rtk pytest tests/strategy_spec tests/strategy_validation tests/adapter_registry tests/instrument_registry tests/strategy_compiler tests/backtest_jobs tests/runtime_events tests/backtest_runner tests/lifecycle tests/strategy_registry tests/promotions tests/web tests/ai_builder tests/integration tests/api tests/auth tests/workflow_spine`.
- [ ] Run frontend tests/build/E2E if dependencies are available.
- [ ] Commit: `verify frontend operator MVP`.

## Master reconciliation after FE-09

- [ ] Run `GIT_MASTER=1 git status --short --branch`.
- [ ] Run full Python verification suite.
- [ ] Run frontend build/tests/E2E or document external dependency blocker.
- [ ] Run targeted anti-drift checks for StrategySpec params, AI lane IDs, ND advisory namespace, Postgres schema, and Redis namespace.
- [ ] Update `README.md` and `AGENTS.md` repo reality if frontend readiness has advanced.
- [ ] Commit any reconciliation docs/tests/code.
- [ ] Push `master`.

## Expected final state

- Operators can complete the MVP path through the frontend.
- Frontend uses HTTP/JSON and SSE, not MCP.
- Strategy params originate from canonical StrategySpec and backend validation.
- AI lane changes preserve `ai_thread_id`, `improvement_cycle_id`, `strategy_lineage_id`, and `strategy_version_id`.
- Postgres stores Builder-owned durable state with stable IDs.
- Redis streams remain Builder-owned and replayable.
- NT receives validated backend-owned config only.
- ND receives advisory/shadow-preview payloads derived from backend stable IDs only.
