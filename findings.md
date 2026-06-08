# Nautilus Builder Deep Review Findings

**Review date:** 2026-06-08
**Scope:** Current repository (`packages/`, `services/`, `apps/web/`, `tests/`, `scripts/`, `doc/`, `docs/`) plus current uncommitted diff.
**Reference repo:** `/home/mok/projects/Nautilus-Daedalus`
**Method:** `$superpowers:code-review`, `nt-review` primary, `nt-architect`/`nt-adapters`/`nt-live`/`nt-testing` supporting, aiogram-dialog negative-inventory lens, official NautilusTrader/EvoMap/LangChain/LangGraph references, static grep, manual route probes, focused tests.

## Executive summary

**Final recommendation:** **REQUEST CHANGES**
**Architectural status:** **BLOCK**
**Primary blocker:** API auth/project scoping is inconsistent: some `/api` routes accept an `authorization` parameter but do not validate it, and strategy mutation routes do not pass `UserProjectContext` into repository mutation methods.

The Builder/Daedalus/NautilusTrader execution boundary remains directionally correct: no Builder production path was found that directly calls `submit_order(` or constructs authoritative `TradeAction(`. The main risk is not live order authority creep; it is cross-project data exposure/mutation and stale review artifacts that previously claimed `APPROVE` despite current blockers.

## Severity summary

| Category | CRITICAL | HIGH | MEDIUM | LOW | WATCH |
|---|---:|---:|---:|---:|---:|
| Security / auth | 0 | 3 | 2 | 0 | 1 |
| Bugs / correctness | 0 | 1 | 2 | 1 | 1 |
| Maintainability | 0 | 0 | 3 | 2 | 2 |
| Architecture / NT alignment | 0 | 1 | 2 | 0 | 4 |
| Legacy / deprecation | 0 | 0 | 2 | 1 | 8 |
| **Total unique actionable findings** | **0** | **4** | **6** | **3** | **8** |

## HIGH priority findings

### H-01 — `/api/strategies` list leaks project-scoped strategies without auth or with wrong-project auth

- **Files:**
  - `services/api/fastapi_app.py:509-511`
  - `services/api/routes/strategies.py:19-24`
  - `packages/strategy_spec/repository.py:79-91`
  - `tests/api/test_fastapi_app.py:266-279`
- **Evidence:** `list_strategies()` never calls `require_context(authorization)` and calls `list_strategies_payload(strategy_repository)` without context. The route helper supports a context but receives none. Existing tests assert that unauthenticated list access returns `200` and exposes `strategy_001`.
- **Manual probe:** After creating an alpha-owned strategy, `GET /api/strategies` with no token returned `200` with `user_id='u1', project_id='p1'`; the same route with a beta token also returned the alpha strategy.
- **Risk:** Cross-tenant/project strategy metadata and full latest spec exposure.
- **Fix:** Require auth on list route, pass `context=context` to `list_strategies_payload()`, and update tests to expect `401` for missing auth and an empty/filtered list for wrong-project tokens.

### H-02 — Strategy approve/clone routes can mutate or copy another project’s strategy

- **Files:**
  - `services/api/fastapi_app.py:541-559`
  - `packages/strategy_spec/repository.py:144-177`
  - `packages/postgres/strategy_repository.py:147-197`
- **Evidence:** `approve_strategy()` and `clone_strategy()` authenticate a token but discard `context`; repository `update_status()`, `approve_strategy()`, and `clone_strategy()` do not scope-check. Postgres variants also ignore context and table rows do not include scope columns in the returned/listed records.
- **Manual probe:** A beta token successfully approved an alpha-owned `strategy_001`; beta clone also returned `201` and created `strategy_002` outside the original scope payload.
- **Risk:** Unauthorized promotion/lifecycle mutation and cross-project copying of strategy specs.
- **Fix:** Add context parameters to repository mutation methods, call `_assert_scope()`/SQL project predicates before mutation, and preserve scope on cloned strategies. Add cross-project negative tests for approve, clone, update-status, Postgres strategy repository paths.

### H-03 — Production auth policy functions exist but FastAPI startup does not enforce them

- **Files:**
  - `packages/auth/policy.py:32-86`
  - `services/api/fastapi_app.py:161-164`, `services/api/fastapi_app.py:680-696`
  - `tests/api/test_production_safety.py:23-31`
- **Evidence:** `validate_builder_env()`, `validate_production_token()`, and `validate_cors_config()` enforce the stronger policy in isolation, but `create_fastapi_app()` does not import/call them. `_register_env_dev_token()` only rejects a small known-dev-token set in production. Existing tests accept `my-secret-prod-key-2026` in production, which is shorter than the 32-character policy requirement.
- **Manual probe:** With `APP_ENV=production`, a durable AI audit SQLite path, and `BUILDER_API_TOKEN=my-secret-prod-key-2026`, FastAPI startup succeeded.
- **Risk:** Production deployments can start with short or public tokens and invalid CORS unless another launcher performs validation.
- **Fix:** Call the policy functions during FastAPI app creation before token registration and CORS middleware setup. Update production tests to require 32+ chars, forbid `NEXT_PUBLIC_BUILDER_API_TOKEN`, reject wildcard/empty CORS in staging/production, and verify startup failure.

### H-04 — Static auth route test gives false confidence

- **Files:**
  - `tests/api/test_route_auth_scope.py:24-71`
  - `services/api/fastapi_app.py:234-252`, `services/api/fastapi_app.py:498-511`
- **Evidence:** The test only checks for an `authorization` parameter or a textual `require_context` occurrence; routes such as adapters, instruments, backtest profile validation, strategy registry external, and strategy list have an auth parameter but do not validate it.
- **Risk:** Future public routes can pass tests while bypassing auth.
- **Fix:** Replace the static source scan with runtime route tests that call each `/api` endpoint without auth and expect `401` unless explicitly allowlisted. Keep health endpoints public only.

## MEDIUM priority findings

### M-01 — Postgres table/schema helpers interpolate unsanitized schema names

- **Files:**
  - `packages/postgres/strategy_repository.py:12-17`
  - `packages/postgres/backtest_job_repository.py:35-40`
  - `packages/postgres/config_repository.py:20`
  - `packages/postgres/adapter_repository.py:17`
  - `packages/postgres/workflow_result_repository.py:25`
  - `packages/postgres/promotion_ledger_repository.py:82`
  - `packages/postgres/migrations.py:80-103`, `packages/postgres/migrations.py:128-292`
- **Evidence:** Several repositories build table identifiers with `f"{self._schema}.{name}"` without applying `safe_storage_identifier()`. Current callers normally use constant `builder`, so this is not an immediate exploit in the reviewed path.
- **Risk:** SQL injection or broken migrations if schema becomes operator-controlled or CLI-provided.
- **Fix:** Centralize a Postgres identifier helper using the same strict regex as `packages/workflow_spine/storage_config.py:14-17`; validate schema once in constructors and migrations.

### M-02 — `PostgresBacktestJobService.list_jobs_for_strategy()` scans all jobs

- **Files:**
  - `packages/backtest_jobs/postgres_service.py:136-142`
  - `packages/postgres/backtest_job_repository.py:183-190`
- **Evidence:** The repository already has `list_by_strategy_version()`, but the service refreshes all jobs and filters in memory.
- **Risk:** Performance and data-blast-radius issue as job volume grows; unnecessary full-table reads during evidence-summary calls.
- **Fix:** Delegate directly to `self._repo.list_by_strategy_version(strategy_version_id)` and scope by `UserProjectContext` when evidence summary is scoped.

### M-03 — Evidence summary can overstate compile evidence

- **Files:**
  - `services/api/routes/evidence_summary.py:59-67`, `services/api/routes/evidence_summary.py:110-115`
  - `packages/backtest_jobs/models.py:31-33`
  - `scripts/seed_demo_evidence.py:33-36`
- **Evidence:** If strategy status is `backtested`, `approved`, or `execution_ready`, compile status becomes `passed` even without a compile hash. `BacktestJob.compile_hash` accepts any string, and demo seed values use `sha256:demo_*` strings rather than 64-hex digests.
- **Risk:** UI can present implied compile evidence as equivalent to artifact-backed compile evidence.
- **Fix:** Split statuses: `passed_with_artifact`, `passed_inferred`, `missing`; validate production compile hashes as 64-hex or store `hash_scheme` explicitly. Keep demo hashes labelled `fixture_dev_only`/`demo_only`.

### M-04 — Strategy Postgres repository does not preserve/project-scope filter list/detail/mutations

- **Files:**
  - `packages/postgres/strategy_repository.py:27-42`, `packages/postgres/strategy_repository.py:111-145`, `packages/postgres/strategy_repository.py:147-197`
  - `packages/postgres/migrations.py:24-40`
- **Evidence:** The in-memory repository tracks `_scopes`; Postgres strategy rows insert no `user_id`/`project_id`, list/detail methods ignore context, and mutations do not scope-filter.
- **Risk:** Once Postgres mode is used, API-level context cannot be enforced consistently for strategies.
- **Fix:** Add scoped columns to `strategies` and `strategy_versions`, migrate existing demo/default rows with explicit local scope, and apply context predicates in list/detail/mutations.

### M-05 — Oversized modules concentrate too many responsibilities

- **Files:**
  - `services/api/fastapi_app.py` — 753 LOC
  - `packages/execution_lane/sessions.py` — 434 LOC
  - `packages/ai_builder/provider.py` — 334 LOC
  - `apps/web/components/config/ExecutionLaneFeaturePanel.tsx` — 678 LOC
  - `apps/web/lib/api.ts` — 438 LOC
- **Risk:** Auth omissions and route ownership drift are easier to introduce when route registration, policy, dependency construction, and handlers live in one large file.
- **Fix:** Split route groups into routers with typed dependencies; keep `fastapi_app.py` as composition/bootstrap only. For frontend, split large panels into view-model, sections, and API hooks.

### M-06 — AI audit persists raw prompts without a redaction gate

- **Files:**
  - `packages/ai_builder/service.py:76-87`
- **Evidence:** The audit store records the raw `prompt`. `_reject_forbidden_prompt()` blocks obvious credential terms but not all sensitive operator content.
- **Risk:** Prompt audit logs may store secrets or proprietary strategy details longer than intended.
- **Fix:** Add a prompt-redaction/secrets scan before persistence; store a redacted prompt plus hash of the original if forensic traceability is needed.

## LOW priority findings

### L-01 — Demo seed silently swallows strategy upsert errors

- **File:** `scripts/seed_builder_demo_data.py:76-80`
- **Risk:** Broken migrations/schema mismatches can be hidden, followed by an unconditional status update that may fail later or partially seed data.
- **Fix:** Catch only the expected idempotency conflict or log/re-raise unexpected exceptions.

### L-02 — Stale review artifacts previously claimed all findings were fixed

- **Files:** `structure.md`, `findings.md`, `handguard.md`
- **Risk:** Operators may treat stale `APPROVE` text as current despite active blockers.
- **Fix:** This update replaces stale approve language with a dated 2026-06-08 REQUEST-CHANGES report.

### L-03 — Current changed diff lacks Postgres-focused evidence summary tests

- **Files:** `tests/api/test_evidence_summary.py`, `packages/backtest_jobs/postgres_service.py`
- **Risk:** Public method behavior is covered for in-memory service but not for the Postgres service/repository path.
- **Fix:** Add a repository mock or lightweight integration test proving `PostgresBacktestJobService.list_jobs_for_strategy()` delegates to `list_by_strategy_version()` and preserves ordering/scope.

## Inventory-first semantic legacy/deprecation closure review

| Item / search term | Status | Evidence | Risk / closure action |
|---|---|---|---|
| `storage_config.py` legacy alias | **OPEN** | `packages/workflow_spine/storage_config.py:1-4` | Deadline remains 2026-07-01. Add issue/owner; remove alias after cutoff. |
| `PostgresWorkflowRepository` alias | **OPEN** | `packages/workflow_spine/postgres_repository.py:194-207` | Alias is intentionally deprecated. Remove after 2026-07-01 and update imports/tests. |
| Backtest legacy hash | **OPEN** | `services/api/routes/backtest_jobs.py:267-275` | Env-flag legacy derivation remains. Add cutoff test and remove after 2026-07-01. |
| `allow_legacy_fixture_refs` | **OPEN** | `services/api/routes/promotions.py:22-34`, `pyproject.toml:36` warning ignore | Strict evidence should be default for non-dev. Remove/deadline the warning suppression after cutoff. |
| `res_001` fixture fallback | **WATCH** | `services/api/routes/workflow_results.py:14-28`, tests under `tests/api/test_workflow_results.py` | Default is gated by `BUILDER_ALLOW_FIXTURE_FALLBACK`; keep production flag off and label fixture evidence. |
| `TradingNode` wording | **WATCH** | `packages/execution_lane/nautilus_runtime.py:11-15`, `packages/execution_lane/sessions.py:137-179`, docs/design text | Label as Python live/integration-specific; do not imply universal current NT live runtime. |
| `LiveNode` wording | **WATCH** | `packages/execution_lane/nautilus_runtime.py:31-32`, official NT data testing docs | Keep Rust `LiveNode` as future/current Rust-backed path; do not claim Builder runs it. |
| `TradeAction` / `submit_order` | **FALSE POSITIVE in Builder production code; WATCH in docs/tests** | Production grep found no `submit_order(` or `TradeAction(`; docs/tests/policy intentionally mention them. | Keep scans specific to code paths, not doc policy text. Reject new production calls. |
| `COINBASE_INTX`, Coinbase International | **CLOSED** | No production references found in current Builder search. | No action. |
| dYdX v3 / `dydx_v3` | **CLOSED** | No production references found in current Builder search. | No action. |
| `fill_limit_at_touch` / `fill_limit_inside_spread` | **CLOSED** | No Builder usage found; Builder backtest config keeps `trade_execution=False`. | Re-check on NT upgrades. |
| `load_ids_async` / `load_async` | **CLOSED/WATCH** | No custom Builder adapter implementation uses these methods. | If Builder adds adapters, follow official adapter guide and DataTester evidence. |
| `builder_fee_refresh_mins` | **CLOSED** | No references found. | No action. |
| `NEXT_PUBLIC_BUILDER_API_TOKEN` | **WATCH** | `apps/web/lib/api.ts:96`, tests, `.env.production.example` forbids it in production. | Accept only for local VM/dev proxy; enforce production startup rejection. |
| `aiogram` / `telegram` | **FALSE POSITIVE for Builder runtime** | No Builder dependency in `pyproject.toml`; docs reference Daedalus Telegram boundary. | Keep as Daedalus-only. Reject Builder aiogram dependency. |
| `langchain` / `langgraph` / `evomap` | **FALSE POSITIVE for Builder runtime** | No Builder dependency in `pyproject.toml`; Daedalus owns these AI lanes. | Keep Builder AI provider advisory-only; do not couple to Daedalus AI runtimes. |
| `fixture` / `fallback` | **WATCH** | Many intentional fixture/dev paths in backtest and workflow results. | Ensure every fixture path is labelled dev/test only and disabled by default in production. |

## NautilusTrader / Daedalus alignment notes

- Builder and Daedalus both pin `nautilus_trader==1.227.0`.
- Official NT adapter docs define layered Rust core + Python integration layers and require DataTester/ExecTester evidence for adapter readiness. Builder currently gates on evidence refs but should not claim it produces those adapter test artifacts.
- Official NT Data Testing Spec notes legacy Python `TradingNode` examples but prefers Rust-backed `LiveNode` for new Rust/PyO3 adapters. Builder docs should retain the `python_live_integration_specific` label for TradingNode contracts.
- Daedalus `AGENTS.md` and README state Telegram is downstream-only, TradeAction is approved intent rather than execution evidence, and ExecutionReport is the source for submitted/filled/rejected/canceled wording. Builder should mirror this boundary.

## Current diff inclusion assessment

**Safe to include with review artifacts, but not production-readiness proof.** The current demo-evidence diff does not introduce Builder order authority or Daedalus coupling. It does introduce/query demo evidence and improves evidence summary encapsulation. Remaining concerns are M-02, M-03, and L-01.

## Verification evidence

```bash
python3 -m compileall -q packages services tests scripts
# pass

python3 -m pytest tests/api/test_evidence_summary.py -q
# 15 passed

python3 -m pytest tests/ -q --tb=line
# 906 passed, 1 skipped, 1 warning

cd apps/web && npm run typecheck
# pass

cd apps/web && npm run build
# pass

cd apps/web && npm run test
# failed: 1 dashboard layout test exceeded the default 5000 ms Vitest timeout under full-suite load

cd apps/web && npx vitest run --config vitest.config.mts --testTimeout=10000
# 115 passed, 4 skipped

python3 -m pytest \
  tests/api/test_fastapi_app.py::test_fastapi_strategy_routes_require_auth_and_filter_by_project \
  tests/api/test_route_auth_scope.py::TestRouteAuthScope::test_all_api_routes_require_auth -q
# 2 passed, but current assertions are insufficient and partly encode H-01.
```

Manual probes confirmed H-01/H-02/H-03. See `structure.md` for the concise probe summary.

## Review verdict

- **code-reviewer recommendation:** REQUEST CHANGES
- **architect status:** BLOCK
- **final recommendation:** REQUEST CHANGES

Do not make production-readiness, merge-ready, or live-readiness claims until H-01 through H-04 are fixed and covered by runtime regression tests.

## Master reconciliation — catalog-backed Nautilus replay

`catalog_backed_replay_smoke` remains recorded as a catalog-backed Nautilus replay smoke: it uses synthetic historical quote ticks and a no-order subscribe strategy to prove BacktestNode wiring. This is **not full trading-production readiness** and must not be used as adapter/live compliance evidence.
