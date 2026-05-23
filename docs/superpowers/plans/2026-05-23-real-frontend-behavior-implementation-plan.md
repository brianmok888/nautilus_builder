# Real Frontend Behavior Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax intentionally. Follow TDD: write/confirm failing behavior tests first, implement minimal code, verify, then commit before moving to the next slice.

## Source design

- Design spec: `docs/superpowers/specs/2026-05-23-real-frontend-behavior-design.md`
- Existing frontend MVP design: `docs/superpowers/specs/2026-05-23-frontend-ready-operator-mvp-design.md`
- Existing scaffold plan to reconcile: `docs/superpowers/plans/2026-05-23-frontend-ready-operator-mvp-implementation-plan.md`
- Source truth docs: `doc/nautilus_builder_spec.md`, `doc/nautilus_builder_hardguards.md`

## Execution rule

Do not count static text, function names, or file-presence tests as completion for real frontend behavior. Each slice must prove real user-visible behavior or backend route behavior.

## File map

### Frontend behavior

- `apps/web/app/layout.tsx` — global nav, safety banner, shell.
- `apps/web/app/page.tsx` — dashboard/entry route.
- `apps/web/app/strategies/page.tsx` — real strategy list and create form.
- `apps/web/app/strategies/[strategyId]/page.tsx` — real detail/version actions.
- `apps/web/app/builder/[strategyId]/page.tsx` — real builder route.
- `apps/web/components/strategy-builder/*` — stateful graph/spec/editor/validation behavior.
- `apps/web/components/market/*` — real adapter/instrument/profile form behavior.
- `apps/web/app/backtests/[jobId]/page.tsx` and `apps/web/components/terminal/*` — real status/events/cancel behavior.
- `apps/web/components/results/*` — real result payload rendering.
- `apps/web/components/ai-builder/*` — real prompt/draft/apply behavior.
- `apps/web/components/promotions/*` — real safe promotion request behavior.
- `apps/web/lib/api.ts`, `apps/web/lib/types.ts` — typed client and DTOs.
- `apps/web/lib/*.test.ts` — TypeScript unit tests for API/helpers/parsers.

### Backend truth required by frontend

- `services/api/app.py` and `services/api/fastapi_app.py` — route parity/status preservation.
- `services/api/routes/*` — status-correct payload helpers.
- `packages/strategy_spec/repository.py` — strategy CRUD/version state.
- `packages/backtest_jobs/service.py` — actual job IDs/status/cancel state.
- `packages/runtime_events/*` — typed event replay/SSE support.
- `packages/ai_builder/*` — advisory apply/audit lane IDs.
- `packages/promotions/*` — safe target/manual approval only.

## Slice 1: API parity, status preservation, and frontend build baseline

- [ ] Write failing Python tests asserting FastAPI and `ApiApp` return matching status codes for create success, validation error, missing strategy, promotion live-target rejection, and backtest job creation.
- [ ] Run the parity tests and confirm RED.
- [ ] Implement shared response/status handling for FastAPI so `ApiResponse.status_code` is preserved.
- [ ] Add route parity guard tests to ensure `ApiApp` and FastAPI register the same public routes.
- [ ] Run parity tests and confirm GREEN.
- [ ] Run `npm install` in `apps/web` if dependencies are absent.
- [ ] Run `npm run typecheck` in `apps/web`; fix TypeScript errors.
- [ ] Run `npm run build` in `apps/web`; fix build errors.
- [ ] Run `rtk pytest tests/api tests/web tests/integration/test_frontend_alignment_guards.py`.
- [ ] Commit: `establish real frontend build and API parity`.

## Slice 2: Real strategy CRUD UI

- [ ] Write failing component/behavior tests for strategy list loading, empty, error, and success states.
- [ ] Write failing tests for create strategy form submission rendering the created strategy.
- [ ] Write failing tests for detail page rendering real version history from API data.
- [ ] Confirm RED.
- [ ] Convert strategies list page to a client/server data-fetching component that actually calls the API.
- [ ] Add create strategy form with disabled/loading/error/success states.
- [ ] Convert strategy detail page to fetch and render lineage/version data.
- [ ] Add save draft and create version actions that call backend helpers.
- [ ] Ensure UI uses stable IDs, not display names, for links/actions.
- [ ] Run frontend tests for strategy pages.
- [ ] Run `rtk pytest tests/api/test_strategies.py tests/web`.
- [ ] Commit: `implement real strategy CRUD UI`.

## Slice 3: Real builder graph/spec state and validation

- [ ] Write failing TypeScript tests for adding blocks, selecting blocks, editing params, graph-to-spec serialization, and unsupported block rejection.
- [ ] Write failing component tests for validation request and error rendering.
- [ ] Confirm RED.
- [ ] Add reducer/store for nodes, edges, selected block, dirty state, spec preview, and validation results.
- [ ] Make block palette add real nodes.
- [ ] Make inspector edit selected node params.
- [ ] Make spec editor display live serialized StrategySpec.
- [ ] Wire validate button to backend validation route.
- [ ] Wire save draft/create version to Strategy CRUD client.
- [ ] Run builder frontend tests plus `rtk pytest tests/strategy_spec tests/strategy_validation tests/api`.
- [ ] Commit: `implement real builder editing flow`.

## Slice 4: Real market/profile form behavior

- [ ] Write failing component tests for fetching adapters, selecting adapter, instrument search, data availability, profile validation success, and validation error.
- [ ] Confirm RED.
- [ ] Implement adapter fetch/render.
- [ ] Implement instrument search using selected adapter.
- [ ] Implement timeframe/date-range/data-type form state.
- [ ] Implement data availability display.
- [ ] Implement profile validation submit and response rendering.
- [ ] Ensure profile result includes stable `adapter_profile_id` or explicit backend identity placeholder until DB-backed profiles exist.
- [ ] Run market/profile frontend tests and `rtk pytest tests/api/test_backtest_profiles.py tests/api/test_market_catalog.py`.
- [ ] Commit: `implement real market profile form`.

## Slice 5: Real backtest job/status/cancel/events behavior

- [ ] Write failing API tests proving created job ID is the service job ID, status reads service state, and cancel transitions service state.
- [ ] Write failing frontend tests for job create, status display, cancel action, and event rendering.
- [ ] Confirm RED.
- [ ] Fix backtest job routes to use `BacktestJobService` state for create/read/cancel.
- [ ] Add typed event payloads instead of `unknown[]`.
- [ ] Add replay endpoint returning actual service/stream events.
- [ ] Add SSE endpoint or a documented polling fallback with identical typed event contract.
- [ ] Implement frontend job status and cancel behavior.
- [ ] Implement terminal commands that call status/log/cancel behavior, not static text.
- [ ] Run `rtk pytest tests/backtest_jobs tests/runtime_events tests/api tests/web` and frontend tests.
- [ ] Commit: `implement real backtest job console`.

## Slice 6: Real results dashboard rendering

- [ ] Write failing frontend tests that result metrics, artifacts, trades, fills, and logs render from payload values.
- [ ] Confirm RED.
- [ ] Implement result data fetch and loading/error/empty states.
- [ ] Render metrics cards.
- [ ] Render artifacts list.
- [ ] Render trades/fills/logs tables or structured lists.
- [ ] Preserve no live execution controls.
- [ ] Run result frontend tests and `rtk pytest tests/api/test_workflow_results.py tests/backtest_runner tests/web`.
- [ ] Commit: `implement real results dashboard rendering`.

## Slice 7: Real advisory AI prompt/apply flow

- [ ] Write failing frontend tests for prompt input, draft submit, validation error display, accepted draft preview, and apply-to-builder behavior.
- [ ] Write failing backend tests if apply/audit lane IDs are incomplete.
- [ ] Confirm RED.
- [ ] Implement prompt form state.
- [ ] Render AI explanation, validation errors, and draft spec.
- [ ] Implement apply-to-builder only for accepted drafts.
- [ ] Preserve `ai_thread_id`, `improvement_cycle_id`, `strategy_lineage_id`, and `strategy_version_id` through API/UI state.
- [ ] Run `rtk pytest tests/ai_builder tests/workflow_spine/test_nd_ai_compatibility.py tests/web tests/api` and frontend tests.
- [ ] Commit: `implement real advisory AI flow`.

## Slice 8: Real safe promotion request flow

- [ ] Write failing frontend tests for promotion context rendering, safe target selection, request submit, success state, error state, and live-target rejection.
- [ ] Confirm RED.
- [ ] Implement promotion form using strategy version/result IDs from props or fetched context.
- [ ] Submit request to backend.
- [ ] Render manual approval status.
- [ ] Ensure live target cannot be selected and backend still rejects it.
- [ ] Run `rtk pytest tests/promotions tests/web tests/api` and frontend tests.
- [ ] Commit: `implement real safe promotion flow`.

## Slice 9: Real composed browser E2E and plan reconciliation

- [ ] Add script to start FastAPI locally for E2E, or document exact command using the current app factory.
- [ ] Configure Playwright `webServer` entries for both backend and Next frontend.
- [ ] Write E2E covering strategy create/list/detail, profile validation, job create/status/cancel or events, result render, AI draft/apply, and promotion request.
- [ ] Run E2E and confirm it actually drives browser interactions, not static existence.
- [ ] Run `npm run typecheck` and `npm run build`.
- [ ] Run full Python suite.
- [ ] Update `docs/verification/2026-05-23-frontend-operator-mvp-verification-report.md` with exact commands and outcomes.
- [ ] Reconcile `docs/superpowers/plans/2026-05-23-frontend-ready-operator-mvp-implementation-plan.md`: check only items truly completed; rename prior scaffold items where necessary.
- [ ] Commit: `verify real frontend operator behavior`.

## Final validation

- [ ] Run full Python suite.
- [ ] Run frontend unit/component tests.
- [ ] Run `npm run typecheck`.
- [ ] Run `npm run build`.
- [ ] Run Playwright E2E or document a specific external blocker.
- [ ] Request review-work validation.
- [ ] Fix any valid review findings.
- [ ] Merge/push to `origin/master`.

## Completion criteria

- Static stub/function-name evidence is no longer the primary proof.
- Real user interactions fetch/submit/render data.
- FastAPI status behavior matches route helper intent.
- Backtest jobs and events use backend state instead of hardcoded IDs.
- TypeScript typecheck and Next build pass.
- Browser E2E proves the operator path or records a concrete environment blocker.
- Plan checkboxes accurately reflect what was actually executed.
