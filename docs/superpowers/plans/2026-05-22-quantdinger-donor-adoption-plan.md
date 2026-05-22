# QuantDinger Donor-Adoption Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax and are intended to be completed in order. Do not skip verification steps. Do not broaden scope. Keep all work inside the Nautilus Builder repository or an isolated worktree created from it.

## Goal

Implement the first Builder-native infrastructure slices from the approved QuantDinger donor-adoption design:

1. `API-01` — real API bootstrap and mounted route adapters.
2. `AUTH-01` — minimal auth/session context and user/project artifact scoping interfaces.

The remaining donor phases (`AGENT-01`, `MCP-01`, `NOTIFY-01`, `DEPLOY-01`) are planned as follow-on milestones, not part of this first executable slice.

## Source Spec

- `docs/superpowers/specs/2026-05-22-quantdinger-donor-adoption-design.md`

## Hard Scope Constraints

- Work only in `nautilus_builder` or an isolated worktree created from it.
- Do not touch the Nautilus-Daedalus repository.
- Do not import or depend on Nautilus-Daedalus source code.
- Do not give Builder live order authority.
- Do not add `TradeAction`, `submit_order`, or live execution routes.
- Keep routes thin; package services remain domain truth.
- Do not implement MCP, notifications, deployment, OAuth, billing, credits, or full RBAC in this first plan.
- Tests first for every behavior change.

## Current Repo Facts

- Route-shaped helpers already exist under `services/api/routes/`.
- Domain logic already exists under `packages/*`.
- There is no real API app bootstrap yet.
- There is no auth/session package yet.
- There is no user/project artifact-scope model yet.
- Tests use pytest via `rtk pytest` and import from `packages.*` / `services.*`.

## File Structure Map

### New API files

- `services/api/__init__.py`
  - Public API package marker.
- `services/api/app.py`
  - Creates the testable API application object.
  - Registers route adapters.
  - Exposes health endpoint.
- `services/api/router.py`
  - Minimal in-process router/test-client abstraction if no web framework is introduced.
  - Keeps this plan dependency-light.
- `services/api/routes/health.py`
  - Health payload adapter.

### New auth files

- `packages/auth/__init__.py`
  - Re-export public auth/session primitives.
- `packages/auth/models.py`
  - `UserProjectContext`, `AuthToken`, `ScopedArtifactRef` models.
- `packages/auth/service.py`
  - Minimal token issuing/verification and project-context lookup.
- `packages/auth/policy.py`
  - Authorization helpers for same-user/same-project checks.

### Tests

- `tests/api/__init__.py`
- `tests/api/test_app_health.py`
- `tests/api/test_route_mounts.py`
- `tests/auth/__init__.py`
- `tests/auth/test_token_context.py`
- `tests/auth/test_project_scope.py`

### Existing files to read, not rewrite unless necessary

- `services/api/routes/ai_builder.py`
- `services/api/routes/runtime_events.py`
- `services/api/routes/strategy_registry.py`
- `services/api/routes/promotions.py`
- `packages/AGENTS.md`
- `services/api/AGENTS.md`
- `tests/AGENTS.md`

## Implementation Tasks

### Task 1 — Prepare isolated execution context

- [ ] Use `superpowers:using-git-worktrees` before editing if not already in an isolated worktree.
- [ ] Create a branch such as `implement-api-auth-foundation`.
- [ ] Confirm `git status --short --branch` is clean before edits.
- [ ] Read `AGENTS.md`, `services/api/AGENTS.md`, `packages/AGENTS.md`, and `tests/AGENTS.md`.

### Task 2 — API-01 red tests: app health and test client

- [ ] Create `tests/api/__init__.py`.
- [ ] Create `tests/api/test_app_health.py`.
- [ ] Write a failing test that imports `create_app` from `services.api.app`.
- [ ] Test that `create_app().get('/health')` returns a JSON-like payload with `status == 'ok'` and `service == 'nautilus_builder_api'`.
- [ ] Run `rtk pytest tests/api/test_app_health.py` and confirm it fails because the app bootstrap does not exist.

### Task 3 — API-01 implementation: minimal app/router

- [ ] Create `services/api/__init__.py`.
- [ ] Create `services/api/router.py` with a tiny testable router object:
  - route registration by method/path;
  - `.get(path)` and `.post(path, json=None)` helpers;
  - response object exposing `status_code` and `.json()`.
- [ ] Create `services/api/routes/health.py` with `health_payload()`.
- [ ] Create `services/api/app.py` with `create_app()`.
- [ ] Register `GET /health`.
- [ ] Run `rtk pytest tests/api/test_app_health.py` and confirm it passes.

### Task 4 — API-01 red tests: mount existing route adapters

- [ ] Create `tests/api/test_route_mounts.py`.
- [ ] Write failing tests for mounted routes that delegate to existing helper functions:
  - `GET /api/runtime-events/replay` returns replay payload list;
  - `GET /api/strategy-registry/external` returns external strategy payloads;
  - `POST /api/ai-builder/draft` returns an advisory draft payload;
  - `POST /api/promotions/shadow` returns a Builder-side promotion payload.
- [ ] Tests must assert no route grants live execution authority.
- [ ] Run `rtk pytest tests/api/test_route_mounts.py` and confirm failure before route mounting.

### Task 5 — API-01 implementation: route mounting

- [ ] Update `services/api/app.py` to register the existing helper modules as routes.
- [ ] Keep route functions thin; do not move package logic into the API layer.
- [ ] Ensure POST route bodies are passed only where needed.
- [ ] Run `rtk pytest tests/api/test_app_health.py tests/api/test_route_mounts.py` and confirm pass.
- [ ] Commit API-01 with message like `add Builder API bootstrap`.

### Task 6 — AUTH-01 red tests: token context

- [ ] Create `tests/auth/__init__.py`.
- [ ] Create `tests/auth/test_token_context.py`.
- [ ] Write failing tests for:
  - issuing a token for `user_id`, `project_id`, and role;
  - verifying the token returns `UserProjectContext`;
  - rejecting an unknown/invalid token;
  - preserving explicit project identity.
- [ ] Run `rtk pytest tests/auth/test_token_context.py` and confirm failure because `packages.auth` does not exist.

### Task 7 — AUTH-01 implementation: minimal auth service

- [ ] Create `packages/auth/__init__.py`.
- [ ] Create `packages/auth/models.py` with strict Pydantic models.
- [ ] Create `packages/auth/service.py` with an in-memory token service:
  - deterministic enough for tests;
  - no production security claims;
  - explicit invalid-token error.
- [ ] Keep this minimal; do not add OAuth/JWT dependencies unless separately justified.
- [ ] Run `rtk pytest tests/auth/test_token_context.py` and confirm pass.

### Task 8 — AUTH-01 red tests: project-scope policy

- [ ] Create `tests/auth/test_project_scope.py`.
- [ ] Write failing tests for:
  - same-project artifact access allowed;
  - cross-project artifact access rejected;
  - user/project ownership represented for `StrategySpec`, `BacktestJob`, `RuntimeEvent`, and `PromotionRequest` artifact refs.
- [ ] Run `rtk pytest tests/auth/test_project_scope.py` and confirm failure before policy implementation.

### Task 9 — AUTH-01 implementation: project-scope policy

- [ ] Create `packages/auth/policy.py`.
- [ ] Implement `assert_same_project(context, artifact_ref)` or equivalent.
- [ ] Use explicit exception/error messages suitable for tests.
- [ ] Do not retrofit every existing package model in this slice; define the interface first.
- [ ] Run `rtk pytest tests/auth` and confirm pass.
- [ ] Commit AUTH-01 with message like `add minimal Builder auth context`.

### Task 10 — Integration and boundary verification

- [ ] Run focused API/auth suite:
  - `rtk pytest tests/api tests/auth`
- [ ] Run broader current suite:
  - `rtk pytest tests/strategy_spec tests/strategy_validation tests/adapter_registry tests/instrument_registry tests/strategy_compiler tests/backtest_jobs tests/runtime_events tests/backtest_runner tests/lifecycle tests/strategy_registry tests/promotions tests/web tests/ai_builder tests/integration tests/api tests/auth`
- [ ] Search changed files for forbidden expansion:
  - `submit_order`
  - `TradeAction`
  - `Daedalus`
  - `billing`
  - `MCP`
- [ ] Confirm no new live execution, billing, MCP, notification, OAuth, or deployment scope was introduced.
- [ ] Commit any test/doc follow-up if needed.

### Task 11 — Follow-on milestone notes

- [ ] If API-01/AUTH-01 are green, add a short note to the implementation summary naming next milestones:
  - `AGENT-01` Builder-safe agent gateway;
  - `MCP-01` thin MCP wrapper;
  - `NOTIFY-01` event-driven notifications;
  - `DEPLOY-01` deployment/config scaffold.
- [ ] Do not implement those follow-on milestones in this plan.

## Verification Commands

Focused:

```bash
rtk pytest tests/api tests/auth
```

Full current suite after implementation:

```bash
rtk pytest tests/strategy_spec tests/strategy_validation tests/adapter_registry tests/instrument_registry tests/strategy_compiler tests/backtest_jobs tests/runtime_events tests/backtest_runner tests/lifecycle tests/strategy_registry tests/promotions tests/web tests/ai_builder tests/integration tests/api tests/auth
```

Boundary search:

```bash
grep -R "submit_order\|TradeAction\|Daedalus\|billing\|MCP" services packages tests
```

## Expected Commit Structure

1. `add Builder API bootstrap`
2. `add minimal Builder auth context`
3. optional small follow-up commit only if review/verification requires it

## Do Not Implement In This Plan

- real frontend app shell;
- real database persistence;
- JWT/OAuth production auth;
- agent gateway;
- MCP server;
- notifications;
- deployment files;
- live execution;
- Nautilus-Daedalus integration code.

## Success Criteria

- `create_app()` exists and mounts current route adapters.
- API route tests pass through the app/test-client abstraction.
- minimal auth context can issue/verify test tokens.
- project-scope policy rejects cross-project artifact access.
- full current suite passes.
- no Builder hardguard is weakened.
