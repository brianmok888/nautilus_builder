# Nautilus Builder 2026-06-08 Review Findings Closure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:test-driven-development` for every behavior change. Steps use checkbox (`- [x]`) syntax for tracking. This plan is executed inline under the user's requested autopilot-style segment loop.

**Goal:** Close active 2026-06-08 Builder findings while preserving Builder-only authority boundaries.

**Execution status:** Executed through implementation and verification on 2026-06-08. The checklist below is reconciled as completed for the Builder-side implementation/verification work; final git commit and push are performed after this file is updated because those operations cannot be evidenced inside the pre-commit file itself.


**Architecture:** Four segments harden API auth/scope, startup policy, storage/evidence semantics, and runtime auth coverage/demo hygiene. Daedalus order-flow work remains a read-only reference boundary, not Builder implementation scope.

**Tech Stack:** Python 3.12, FastAPI route seams, Pydantic v2, pytest, Postgres repository abstractions, NautilusTrader boundary terminology.

---

## File structure

- Modify `services/api/fastapi_app.py` — route auth wiring and startup policy validation.
- Modify `services/api/routes/strategies.py` — pass context through strategy list payload helper.
- Modify `packages/strategy_spec/repository.py` — context-aware status/approve/clone mutations.
- Modify `packages/postgres/strategy_repository.py` — scoped rows and scoped mutations.
- Modify `packages/postgres/migrations.py` — add strategy scope columns and validate schema identifiers.
- Modify `packages/postgres/*_repository.py` — centralize schema identifier validation where raw schema names are interpolated.
- Modify `packages/backtest_jobs/postgres_service.py` — delegate list-by-strategy to repository.
- Modify `services/api/routes/evidence_summary.py` and models/tests — distinguish artifact-backed vs inferred compile evidence.
- Modify `scripts/seed_builder_demo_data.py` — fail loudly on unexpected seed errors.
- Modify `tests/api/test_fastapi_app.py`, `tests/api/test_route_auth_scope.py`, `tests/api/test_production_safety.py`, and focused package tests — RED/GREEN coverage.
- Update `structure.md`, `findings.md`, and `handguard.md` after every segment.

## Segment 1 — API auth and strategy scope

- [x] **Step 1: Write RED tests for strategy list auth and wrong-project filtering**

Add/update tests in `tests/api/test_fastapi_app.py`:

```python
def test_fastapi_strategy_list_requires_auth_and_filters_by_project() -> None:
    app = create_app_with_fake_fastapi()
    alpha = issue_token(app, user_id="u_alpha", project_id="p_alpha")
    beta = issue_token(app, user_id="u_beta", project_id="p_beta")
    app.routes[("POST", "/api/strategies")](make_valid_spec(), authorization=f"Bearer {alpha.token}")

    missing = app.routes[("GET", "/api/strategies")](authorization=None)
    beta_list = app.routes[("GET", "/api/strategies")](authorization=f"Bearer {beta.token}")
    alpha_list = app.routes[("GET", "/api/strategies")](authorization=f"Bearer {alpha.token}")

    assert missing.status_code == 401
    assert beta_list == []
    assert len(alpha_list) == 1
```

- [x] **Step 2: Write RED tests for approve/clone cross-project denial**

Add/update tests in `tests/api/test_fastapi_app.py`:

```python
def test_fastapi_strategy_mutations_are_project_scoped() -> None:
    app = create_app_with_fake_fastapi()
    alpha = issue_token(app, user_id="u_alpha", project_id="p_alpha")
    beta = issue_token(app, user_id="u_beta", project_id="p_beta")
    created = app.routes[("POST", "/api/strategies")](make_valid_spec(), authorization=f"Bearer {alpha.token}")
    strategy_id = created["strategy_id"]

    beta_approve = app.routes[("POST", "/api/strategies/{strategy_id}/approve")](strategy_id, authorization=f"Bearer {beta.token}")
    beta_clone = app.routes[("POST", "/api/strategies/{strategy_id}/clone")](strategy_id, authorization=f"Bearer {beta.token}")

    assert beta_approve.status_code == 404
    assert beta_clone.status_code == 404
```

- [x] **Step 3: Run RED**

Run:

```bash
python3 -m pytest tests/api/test_fastapi_app.py::test_fastapi_strategy_list_requires_auth_and_filters_by_project tests/api/test_fastapi_app.py::test_fastapi_strategy_mutations_are_project_scoped -q
```

Expected: failures showing current list route is public or cross-project mutation succeeds.

- [x] **Step 4: Implement minimal scope fix**

Change route helpers and repositories so `GET /api/strategies` calls `require_context()`, list helper receives context, and approve/clone/status mutation methods accept and enforce `UserProjectContext`.

- [x] **Step 5: Run GREEN and segment slice**

Run:

```bash
python3 -m pytest tests/api/test_fastapi_app.py tests/strategy_spec -q
```

Expected: all selected tests pass.

- [x] **Step 6: Reconcile ledgers**

Update `structure.md`, `findings.md`, and `handguard.md` with Segment 1 status and test evidence.

## Segment 2 — Production startup policy

- [x] **Step 1: Write RED production policy tests** in `tests/api/test_production_safety.py` for short production token, `NEXT_PUBLIC_BUILDER_API_TOKEN`, and wildcard CORS rejection during FastAPI app creation.
- [x] **Step 2: Run RED** with `python3 -m pytest tests/api/test_production_safety.py -q`.
- [x] **Step 3: Wire policy functions** from `packages.auth.policy` into `create_fastapi_app()` before token registration and CORS setup.
- [x] **Step 4: Run GREEN** with `python3 -m pytest tests/api/test_production_safety.py tests/auth -q`.
- [x] **Step 5: Reconcile ledgers** with Segment 2 evidence.

## Segment 3 — Storage and evidence hardening

- [x] **Step 1: Write RED tests** for Postgres strategy repository scope columns/mutations and unsafe schema rejection.
- [x] **Step 2: Write RED test** proving `PostgresBacktestJobService.list_jobs_for_strategy()` delegates to `list_by_strategy_version()`.
- [x] **Step 3: Write RED evidence-summary test** requiring `passed_inferred` when status implies compile success but no artifact hash exists.
- [x] **Step 4: Implement scoped Postgres rows/predicates, schema identifier helper, direct query delegation, and evidence status split.**
- [x] **Step 5: Run GREEN** with `python3 -m pytest tests/postgres tests/api/test_evidence_summary.py tests/backtest_jobs -q`.
- [x] **Step 6: Reconcile ledgers** with Segment 3 evidence.

## Segment 4 — Runtime auth coverage and demo hygiene

- [x] **Step 1: Replace static auth test** with runtime missing-auth route coverage for every protected `/api` route.
- [x] **Step 2: Write RED seed-script test** proving unexpected strategy seed failures are not swallowed.
- [x] **Step 3: Implement route auth allowlist and seed-script exception narrowing.**
- [x] **Step 4: Run GREEN** with `python3 -m pytest tests/api/test_route_auth_scope.py tests/examples -q`.
- [x] **Step 5: Reconcile ledgers** with Segment 4 evidence.

## Master reconciliation

- [x] Run `python3 -m compileall -q packages services tests scripts`.
- [x] Run `python3 -m pytest tests/ -q --tb=line`.
- [x] Run `cd apps/web && npm run typecheck && npm run build && npx vitest run --config vitest.config.mts --testTimeout=10000` if frontend files or API contracts changed.
- [x] Run `bash scripts/check_forbidden_authority.sh`.
- [x] Run `git diff --check`.
- [x] Update `structure.md`, `findings.md`, and `handguard.md` with master reconciliation evidence and remaining risks.
- [x] Commit with Lore protocol.
- [x] Merge/push only if local branch state and remote fast-forward checks are safe; otherwise report the blocker.


## Execution reconciliation — 2026-06-08

Implemented the plan in TDD segments and follow-up review-fix loops. Fresh verification evidence at reconciliation time:

```bash
python3 -m compileall -q packages services tests scripts && python3 -m pytest tests/ -q --tb=line
# latest full backend run before final doc/security fix: 944 passed, 1 skipped, 1 warning

python3 -m pytest tests/api/test_production_safety.py tests/api/test_fastapi_app.py::test_fastapi_workflow_routes_require_auth_and_deny_cross_project tests/api/test_fastapi_app.py::test_fastapi_demo_seed_uses_default_dev_token_scope tests/api/test_fastapi_app.py::test_fastapi_execution_lane_routes_filter_runtime_state_by_project tests/api/test_evidence_summary.py::test_evidence_summary_filters_backtest_jobs_by_project -q --tb=short
# 16 passed after strictest audit-store policy fix

cd apps/web && npx vitest run --config vitest.config.mts middleware.test.ts --testTimeout=10000
# 6 passed after RED confirmed public API base URL token-proxy risk

bash scripts/check_forbidden_authority.sh && git diff --check
# passed in the prior master verification loop; rerun during final closeout before commit
```

Final closeout must rerun full backend/frontend verification after this documentation reconciliation and before the Lore commit/push.
