# Frontend Contract Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax and are intended to be completed in order. Do not skip verification steps. Do not broaden scope. Keep all work inside the Nautilus Builder repository or an isolated worktree created from it.

## Goal

Implement the first contract-first frontend foundation slice from the approved frontend stack/adaptation design.

This plan does **not** scaffold a real Next.js app. It defines executable Python-backed contracts and matching placeholder frontend documentation so a later frontend scaffold can safely use Next.js + React + TypeScript without weakening Builder hardguards.

## Source Spec

- `docs/superpowers/specs/2026-05-22-frontend-stack-adaptation-design.md`

## Hard Scope Constraints

- Work only in `nautilus_builder` or an isolated worktree created from it.
- Do not touch the Nautilus-Daedalus repository.
- Do not add a frontend package manifest, Next.js app shell, bundler config, or real framework runtime in this plan.
- Do not copy QuantDinger-Vue code.
- Do not add quick-trade, broker credential, billing, live order, Daedalus control, or browser-side execution UI.
- Frontend contracts may hide/show UI affordances, but backend API/auth remains authoritative.
- Tests first for every behavior change.

## Current Repo Facts

- API/auth foundation exists under `services/api/*` and `packages/auth/*`.
- Placeholder TSX components exist under `apps/web/components/*`.
- Python-backed UI contracts already exist under `packages/ui_contracts/*`.
- `tests/web/*` verifies UI boundary behavior without a frontend runner.
- There is no real frontend app runtime yet.

## File Structure Map

### New contract package files

- `packages/frontend_contracts/__init__.py`
  - Public exports for frontend integration contracts.
- `packages/frontend_contracts/api_client.py`
  - Defines allowed frontend API client endpoints and forbidden endpoint categories.
- `packages/frontend_contracts/auth_flow.py`
  - Defines frontend session/auth state transitions against backend-owned auth.
- `packages/frontend_contracts/route_guards.py`
  - Defines route access rules for authenticated workspace and forbidden capability routes.
- `packages/frontend_contracts/surfaces.py`
  - Maps safe Builder feature surfaces to backend API groups.

### New documentation/artifact files

- `apps/web/components/FRONTEND_CONTRACTS.md`
  - Human-readable contract note for future frontend implementation.

### Tests

- `tests/frontend_contracts/__init__.py`
- `tests/frontend_contracts/test_api_client_contract.py`
- `tests/frontend_contracts/test_auth_flow_contract.py`
- `tests/frontend_contracts/test_route_guard_contract.py`
- `tests/frontend_contracts/test_surface_map.py`

## Implementation Tasks

### Task 1 — Prepare isolated execution context

- [ ] Use `superpowers:using-git-worktrees` before editing if not already in an isolated worktree.
- [ ] Create a branch such as `implement-frontend-contract-foundation`.
- [ ] Confirm `git status --short --branch` is clean before edits.
- [ ] Read `AGENTS.md`, `apps/web/components/AGENTS.md`, `packages/AGENTS.md`, and `tests/AGENTS.md`.

### Task 2 — Red tests: API client endpoint contract

- [ ] Create `tests/frontend_contracts/__init__.py`.
- [ ] Create `tests/frontend_contracts/test_api_client_contract.py`.
- [ ] Write failing tests asserting the frontend API contract exposes safe groups:
  - `auth`;
  - `strategy_specs`;
  - `validation`;
  - `backtest_jobs`;
  - `runtime_events`;
  - `ai_drafts`;
  - `promotion_readiness`.
- [ ] Write failing tests asserting forbidden categories are absent:
  - `quick_trade`;
  - `live_orders`;
  - `broker_credentials`;
  - `billing`;
  - `daedalus_control`;
  - `browser_python_execution`.
- [ ] Run `rtk pytest tests/frontend_contracts/test_api_client_contract.py` and confirm RED because `packages.frontend_contracts` does not exist.

### Task 3 — Implement API client contract

- [ ] Create `packages/frontend_contracts/__init__.py`.
- [ ] Create `packages/frontend_contracts/api_client.py` with strict data structures or Pydantic models.
- [ ] Include endpoint names and backend route/path references only; do not create real browser code.
- [ ] Run `rtk pytest tests/frontend_contracts/test_api_client_contract.py` and confirm GREEN.

### Task 4 — Red tests: auth/session frontend flow

- [ ] Create `tests/frontend_contracts/test_auth_flow_contract.py`.
- [ ] Write failing tests for:
  - unauthenticated initial state;
  - login success stores user/project context;
  - unauthorized response clears local state;
  - frontend state never grants backend permissions by itself.
- [ ] Run the focused test and confirm RED before implementation.

### Task 5 — Implement auth/session flow contract

- [ ] Create `packages/frontend_contracts/auth_flow.py`.
- [ ] Implement minimal state transition helpers/models.
- [ ] Reference `packages.auth.UserProjectContext` where useful, without coupling frontend to token internals.
- [ ] Run `rtk pytest tests/frontend_contracts/test_auth_flow_contract.py` and confirm GREEN.

### Task 6 — Red tests: route guard contract

- [ ] Create `tests/frontend_contracts/test_route_guard_contract.py`.
- [ ] Write failing tests for:
  - unauthenticated workspace route denied;
  - authenticated workspace route allowed;
  - forbidden live-order/credential/billing/Daedalus-control routes denied even when authenticated;
  - route guards are marked as UX safety rails, not backend policy authority.
- [ ] Run the focused test and confirm RED before implementation.

### Task 7 — Implement route guard contract

- [ ] Create `packages/frontend_contracts/route_guards.py`.
- [ ] Implement route classification and guard decision helpers.
- [ ] Keep error/decision strings explicit and deterministic.
- [ ] Run `rtk pytest tests/frontend_contracts/test_route_guard_contract.py` and confirm GREEN.

### Task 8 — Red tests: safe surface map

- [ ] Create `tests/frontend_contracts/test_surface_map.py`.
- [ ] Write failing tests that safe surfaces map to backend API groups:
  - Strategy Builder;
  - Validation Report;
  - Backtest Job Console;
  - Runtime Event Terminal;
  - AI Draft Panel;
  - Promotion Readiness View.
- [ ] Write failing tests that no safe surface maps to direct package internals or Daedalus source.
- [ ] Run the focused test and confirm RED before implementation.

### Task 9 — Implement safe surface map

- [ ] Create `packages/frontend_contracts/surfaces.py`.
- [ ] Implement a deterministic safe-surface registry.
- [ ] Ensure every surface references API client groups rather than package internals.
- [ ] Run `rtk pytest tests/frontend_contracts/test_surface_map.py` and confirm GREEN.

### Task 10 — Add frontend contract documentation artifact

- [ ] Create `apps/web/components/FRONTEND_CONTRACTS.md`.
- [ ] State that QuantDinger-Vue is a pattern donor only.
- [ ] State that the selected target stack is Next.js + React + TypeScript.
- [ ] List safe surfaces and forbidden surfaces.
- [ ] State that Daedalus adaptation is backend-contract-only.

### Task 11 — Verification and boundary checks

- [ ] Run focused suite:
  - `rtk pytest tests/frontend_contracts`
- [ ] Run broader suite:
  - `rtk pytest tests/api tests/auth tests/web tests/frontend_contracts`
- [ ] Run full current suite if time/tool budget permits:
  - `rtk pytest tests/strategy_spec tests/strategy_validation tests/adapter_registry tests/instrument_registry tests/strategy_compiler tests/backtest_jobs tests/runtime_events tests/backtest_runner tests/lifecycle tests/strategy_registry tests/promotions tests/web tests/ai_builder tests/integration tests/api tests/auth tests/frontend_contracts`
- [ ] Search changed files for forbidden expansion:
  - `quick_trade`
  - `live_orders`
  - `broker_credentials`
  - `billing`
  - `Daedalus`
  - `Pyodide`
- [ ] Confirm any hits are only forbidden-list or explanatory documentation hits.

### Task 12 — Commit structure

- [ ] Commit contract package and tests as `add frontend contract foundation`.
- [ ] Commit documentation artifact as `document frontend contract boundaries` if separate from code changes.

## Verification Commands

Focused:

```bash
rtk pytest tests/frontend_contracts
```

Broader frontend/API/auth slice:

```bash
rtk pytest tests/api tests/auth tests/web tests/frontend_contracts
```

Full current suite:

```bash
rtk pytest tests/strategy_spec tests/strategy_validation tests/adapter_registry tests/instrument_registry tests/strategy_compiler tests/backtest_jobs tests/runtime_events tests/backtest_runner tests/lifecycle tests/strategy_registry tests/promotions tests/web tests/ai_builder tests/integration tests/api tests/auth tests/frontend_contracts
```

Boundary search:

```bash
grep -R "quick_trade\|live_orders\|broker_credentials\|billing\|Daedalus\|Pyodide" packages/frontend_contracts tests/frontend_contracts apps/web/components/FRONTEND_CONTRACTS.md
```

## Expected Commit Structure

1. `add frontend contract foundation`
2. `document frontend contract boundaries`

## Do Not Implement In This Plan

- real Next.js app scaffold;
- package manifest;
- frontend build/test runner;
- copied QuantDinger-Vue code;
- live trading UI;
- credential UI;
- billing UI;
- Daedalus control UI.

## Success Criteria

- frontend API client contract exists and excludes forbidden capability groups;
- auth/session frontend flow contract exists and preserves backend authority;
- route guard contract exists and blocks unsupported capabilities;
- safe UI surface map exists and references API groups, not package internals;
- documentation artifact tells future frontend workers what is safe to build;
- all focused and broader verification commands pass.
