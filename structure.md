# Nautilus Builder Structure Review

**Review date:** 2026-06-08
**Target repository:** `/home/mok/projects/nautilus_builder`
**Reference repository:** `/home/mok/projects/Nautilus-Daedalus`
**Review mode:** `$superpowers:code-review` routed through `$superpowers:nt-review` (primary) with `nt-architect`, `nt-adapters`, `nt-live`, `nt-testing`, and `aiogram-dialog-menus` as supporting boundary lenses.
**Current verdict:** **APPROVE FOR BUILDER-ONLY DEV-DEMO CLOSEOUT** — hash styling, DOM-order coverage, verification docs, scoped demo seed, local DB smoke, and safety checks are verified. Production/live trading readiness remains out of scope.

## Authoritative references checked

- NautilusTrader official repo: <https://github.com/nautechsystems/nautilus_trader>
- NautilusTrader Developer Guide: <https://nautilustrader.io/docs/latest/developer_guide>
- NautilusTrader Adapters guide: <https://nautilustrader.io/docs/latest/developer_guide/adapters/>
- NautilusTrader Data Testing Spec: <https://nautilustrader.io/docs/latest/developer_guide/spec_data_testing/>
- NautilusTrader Execution Testing Spec: <https://nautilustrader.io/docs/latest/developer_guide/spec_exec_testing/>
- EvoMap Evolver: <https://github.com/EvoMap/evolver>
- LangChain: <https://github.com/langchain-ai/langchain>
- LangGraph: <https://github.com/langchain-ai/langgraph>
- Daedalus local reference: `/home/mok/projects/Nautilus-Daedalus`

## Repository shape (current tracked surface)

`git ls-files packages services apps/web tests scripts doc docs` reports **542 tracked files** across the review surface:

| Area | Tracked files | Role |
|---|---:|---|
| `packages/` | 136 | Canonical Python domain layer: strategy specs, validation, compiler, backtests, execution lane, auth, AI builder, stores, Postgres seams. |
| `services/` | 25 | FastAPI and lightweight API adapter layers plus backend worker stubs. |
| `apps/web/` | 121 | Next.js 15 / React 19 / Ant Design 6 operator UI. Must remain observational and backend-driven. |
| `tests/` | 178 | Contract and regression suite. Several tests currently encode known auth-scope gaps. |
| `scripts/` | 8 | Local/dev/demo orchestration and seed scripts. |
| `doc/` | 13 | Product/runtime source truth. |
| `docs/` | 61 | Derived runbooks, implementation artifacts, deployment/verification docs. |

## Boundary model

| Boundary | Current status | Evidence / notes |
|---|---|---|
| Builder vs live order authority | **Aligned** | `packages/strategy_validation/policy.py` blocks `submit_order`, `TradeAction`, credential terms; `packages/backtest_runner/config_builder.py` rejects credentials; execution lane payloads keep `may_submit_order=False` in paper paths. |
| Builder vs Daedalus | **Aligned but needs wording discipline** | Daedalus owns live execution, TradeAction intent, ExecutionReport, Telegram delivery, EvoMap/LangGraph decision lanes. Builder must only produce specs, validation/compile/backtest evidence, and reviewed handoff artifacts. |
| NautilusTrader version | **Aligned** | Builder `pyproject.toml` pins `nautilus_trader==1.227.0`; Daedalus `pyproject.toml` also pins `1.227.0`. |
| NT adapter readiness claims | **WATCH** | Official adapter docs require Rust/Python adapter layers and DataTester/ExecTester evidence. Builder can gate on evidence refs but must not claim it produces adapter compliance evidence. |
| Python `TradingNode` / Rust `LiveNode` wording | **WATCH** | Builder uses Python `TradingNode` as an integration-specific paper/runtime contract; docs should not present it as the universal current live runtime. Rust-backed `LiveNode` remains the future/current Rust v2 path. |
| AI/EvoMap/LangChain/LangGraph | **Aligned** | Builder does not depend on EvoMap/LangChain/LangGraph in `packages/`, `services/`, or `pyproject.toml`; it uses an OpenAI-compatible advisory provider and validates outputs before acceptance. |
| aiogram-dialog / Telegram | **Aligned** | Builder has no aiogram/aiogram-dialog dependency. Daedalus owns Telegram dialog/runtime paths; Builder docs may reference this only as an external downstream notification boundary. |
| Frontend vs runtime authority | **Aligned with caveats** | UI carries API token handling for local VM mode and no direct order authority; browser must never collect exchange credentials or own worker/runtime handles. |
| API project scoping | **SEGMENTS 1 + 4 CLOSED** | Strategy list/mutation routes require scoped context, and runtime missing-auth tests now cover every registered FastAPI `/api/*` route. |

## High-level architecture map

```text
nautilus_builder/
├── doc/                         # Product/runtime source truth
├── docs/                        # Derived runbooks, verification, deployment docs
├── packages/
│   ├── strategy_spec/           # StrategySpec schema, repositories, demo seed data
│   ├── strategy_validation/     # Builder hard-rule validation and forbidden references
│   ├── strategy_compiler/       # StrategySpec -> compile artifacts/profiles
│   ├── ai_builder/              # Advisory AI draft generation + audit storage
│   ├── backtest_runner/         # NT BacktestEngine/BacktestNode smoke and run contracts
│   ├── backtest_jobs/           # Backtest job lifecycle service
│   ├── execution_lane/          # Backend-owned TradingNode paper/live contract models
│   ├── workflow_spine/          # Workflow lineage/result storage seams
│   ├── runtime_events/          # Runtime event stream seams
│   ├── adapter_registry/        # Builder-approved adapter profiles
│   ├── auth/                    # Token, project scope, policy, audit/rate-limit helpers
│   └── postgres/                # Postgres migrations/repositories
├── services/api/                # FastAPI route adapter layer over packages/*
├── services/workers/            # Backend-only worker entrypoints
├── apps/web/                    # Observational operator UI
├── scripts/                     # Local/dev seed and run helpers
└── tests/                       # Contract-first regression suite
```

## Current changed-diff assessment

The current uncommitted diff is a findings-closure hardening set, not only a demo-evidence change. It closes the reviewed auth/scope/startup/storage/evidence issues while preserving Builder-only authority boundaries.

| Diff area | Assessment |
|---|---|
| FastAPI route/auth layer | Strategy, workflow result, evidence-summary, and execution-lane routes now require bearer context and enforce project scope where records or runtime state are project-owned. |
| Startup policy | `create_fastapi_app()` validates production/staging token and CORS policy before app startup; strictest configured `BUILDER_ENV`/`APP_ENV` wins, and `BUILDER_DEV_AUTH_TOKEN` is rejected outside local mode. |
| Evidence/storage | Postgres identifiers are validated before interpolation; evidence summary distinguishes `passed_inferred` from artifact-backed compile evidence and filters backtest jobs by `UserProjectContext`. |
| Demo seeding | Demo strategies/evidence seed under the configured dev user/project scope and no longer swallow unexpected strategy save failures. |
| Web proxy | Next middleware injects server-side API auth only in local mode and now ignores `NEXT_PUBLIC_API_BASE_URL` for token-proxy destinations. Staging/production compose files do not pass `BUILDER_API_TOKEN` to the web service. |
| Docs/tests | Route matrix tests cover every registered FastAPI `/api/*` route, focused regression tests cover review blockers, and runbooks now use same-origin server-side web proxying instead of browser-held tokens. |

No direct `submit_order(` or authoritative `TradeAction(` call was found in production Builder code during the review scan. `TradeAction`/`submit_order` references are expected in docs/tests/policy text and Daedalus boundary references.

## Verification evidence collected during current closure

```bash
python3 -m compileall -q packages services tests scripts && python3 -m pytest tests/ -q --tb=line
# 944 passed, 1 skipped, 1 warning

bash scripts/check_forbidden_authority.sh && git diff --check
# passed

cd apps/web && rm -rf .next && npm run build
# passed; route summary includes Middleware

cd apps/web && npm run typecheck && npx vitest run --config vitest.config.mts --testTimeout=10000
# 120 passed, 4 skipped

cd apps/web && npx vitest run --config vitest.config.mts middleware.test.ts --testTimeout=10000
# 6 passed after RED confirmed public API base URL proxy risk
```

Former manual-probe failures for unauthenticated strategy list access, wrong-project strategy list access, wrong-project approve/clone, short production token startup, `/api/results` list leakage, evidence-summary cross-project job leakage, and execution-lane project-scope bypass are now represented by regression tests.

## Stop condition for this review

This review is complete for Builder-only dev-demo closeout when final git/remote checks pass. The repo is **not** production/live-trading ready; adapter/live readiness still requires DataTester/ExecTester/reconciliation evidence outside this sprint.

## Master reconciliation — catalog-backed Nautilus replay

`catalog_backed_replay_smoke` writes synthetic historical quote ticks into a `ParquetDataCatalog` and runs NautilusTrader `BacktestNode` with the official no-order subscribe strategy. This is Builder evidence that the pinned Nautilus runtime can replay catalog data through the backtest data path; it is **not full trading-production readiness** and does not replace DataTester/ExecTester/reconciliation evidence for adapters or live execution.


## Segment 1 reconciliation — API auth and strategy scope

**Completed:** 2026-06-08

Implemented and verified the first closure segment for strategy API auth and project scope. `GET /api/strategies` now requires bearer auth and passes `UserProjectContext` to the strategy repository. Strategy approve/clone/status paths now accept scoped context and cannot mutate another project in the in-memory repository. The Postgres strategy repository now persists `user_id`/`project_id`, filters scoped list/detail/version reads, accepts context on approve/clone/status mutations, and includes an idempotent migration v5 for existing databases while v1 creates scoped columns for fresh databases.

Verification evidence:

```bash
python3 -m pytest tests/api/test_fastapi_app.py::test_fastapi_strategy_routes_require_auth_and_filter_by_project tests/api/test_fastapi_app.py::test_fastapi_strategy_approve_and_clone_are_project_scoped -q
# 2 passed

python3 -m pytest tests/api/test_fastapi_app.py tests/strategy_spec tests/postgres/test_strategy_repository.py tests/postgres/test_migration_v2.py -q
# 75 passed

python3 -m compileall -q packages/strategy_spec/repository.py packages/postgres/strategy_repository.py packages/postgres/migrations.py services/api/fastapi_app.py tests/api/test_fastapi_app.py tests/postgres/test_strategy_repository.py
# pass
```

At Segment 1 completion time, remaining blockers were H-03 production startup policy wiring, H-04 runtime auth coverage, and medium storage/evidence findings.


## Segment 2 reconciliation — production startup policy

**Completed:** 2026-06-08

Implemented and verified FastAPI startup enforcement for the existing `packages.auth.policy` checks. `create_fastapi_app()` now validates `BUILDER_ENV`/`APP_ENV`, rejects staging/production without a 32+ character `BUILDER_API_TOKEN`, rejects `NEXT_PUBLIC_BUILDER_API_TOKEN`, and rejects empty or wildcard CORS origins before registering tokens or accepting traffic. Local/dev token behavior remains covered by tests.

Verification evidence:

```bash
python3 -m pytest tests/api/test_production_safety.py tests/api/test_security_hardening.py tests/auth -q
# 67 passed, 1 warning (Starlette/httpx deprecation from testclient)

python3 -m pytest tests/api/test_fastapi_app.py tests/api/test_production_safety.py tests/api/test_security_hardening.py tests/auth -q
# 84 passed, 1 warning (Starlette/httpx deprecation from testclient)

python3 -m compileall -q services/api/fastapi_app.py tests/api/test_production_safety.py
# pass
```

At Segment 2 completion time, remaining blockers were H-04 runtime auth coverage and storage/evidence reconciliation pending Segment 3.


## Segment 3 reconciliation — storage and evidence hardening

**Completed:** 2026-06-08

Implemented and verified Postgres storage/evidence hardening. A central `packages.postgres.identifiers` helper now rejects unsafe schema/table identifiers for Postgres repositories, migration entrypoints, default seed helpers, and the demo seed script before SQL is built. `PostgresBacktestJobService.list_jobs_for_strategy()` now delegates to `PostgresBacktestJobRepository.list_by_strategy_version()` instead of refreshing/scanning all jobs. Evidence summary now reports lifecycle-only compile success as `passed_inferred` unless an artifact hash is present. The demo seed script now reuses the canonical demo `StrategySpec` factory and surfaces unexpected strategy upsert failures instead of swallowing them.

Verification evidence:

```bash
python3 -m pytest tests/postgres/test_identifier_safety.py tests/backtest_jobs/test_postgres_service.py tests/api/test_evidence_summary.py::test_backtested_strategy_has_compile_evidence tests/api/test_evidence_summary.py::test_compile_status_inferred_from_lifecycle_does_not_create_compile_audit tests/scripts/test_seed_builder_demo_data.py -q
# 15 passed

python3 -m pytest tests/postgres tests/api/test_evidence_summary.py tests/backtest_jobs tests/scripts/test_seed_builder_demo_data.py -q
# 101 passed

python3 -m compileall -q packages/postgres packages/backtest_jobs/postgres_service.py services/api/routes/evidence_summary.py scripts/seed_builder_demo_data.py tests/postgres/test_identifier_safety.py tests/backtest_jobs/test_postgres_service.py tests/scripts/test_seed_builder_demo_data.py tests/api/test_evidence_summary.py
# pass
```

At final closeout time, Segment 3 is reconciled; production compile-hash strictness remains WATCH only for future non-demo promotion evidence.


## Segment 4 reconciliation — runtime auth coverage

**Completed:** 2026-06-08

Implemented and verified runtime missing-auth coverage for every registered FastAPI `/api/*` route. The old static source-scan test was replaced with a route matrix that fails if a new `/api/*` route is mounted without an explicit runtime auth assertion. The six previously public FastAPI catalog/profile/registry routes now call `require_context()` before returning data.

Verification evidence:

```bash
python3 -m pytest tests/api/test_route_auth_scope.py::TestRouteAuthScope::test_every_registered_api_route_is_auth_tested tests/api/test_route_auth_scope.py::TestRouteAuthScope::test_protected_api_routes_reject_missing_auth_at_runtime -q
# 2 passed

python3 -m pytest tests/api/test_route_auth_scope.py tests/api/test_fastapi_app.py tests/api/test_production_safety.py tests/api/test_security_hardening.py tests/auth -q
# 91 passed, 1 skipped, 1 warning (Starlette/httpx deprecation from testclient)

python3 -m compileall -q services/api/fastapi_app.py tests/api/test_route_auth_scope.py
# pass
```

At final closeout time, full master reconciliation, architecture review follow-up, and verification have passed for the Builder-only dev-demo scope; safe git push/merge checks remain.

## Master reconciliation — findings closure implementation

**Updated:** 2026-06-08

Master reconciliation verifies the completed Segment 1-4 closure plus follow-up review fixes as a whole. The current diff now covers API auth/scope, production startup policy, durable AI audit-store policy, Postgres identifier/evidence semantics, runtime route auth coverage, execution-lane project scoping, local-only web token proxying, and required ledger/runbook updates.

Verification evidence:

```bash
python3 -m compileall -q packages services tests scripts && python3 -m pytest tests/ -q --tb=line
# 944 passed, 1 skipped, 1 warning

python3 -m pytest tests/api/test_production_safety.py tests/api/test_fastapi_app.py::test_fastapi_workflow_routes_require_auth_and_deny_cross_project tests/api/test_fastapi_app.py::test_fastapi_demo_seed_uses_default_dev_token_scope tests/api/test_fastapi_app.py::test_fastapi_execution_lane_routes_filter_runtime_state_by_project tests/api/test_evidence_summary.py::test_evidence_summary_filters_backtest_jobs_by_project -q --tb=short
# 16 passed after strictest audit-store policy fix

bash scripts/check_forbidden_authority.sh && git diff --check
# passed in the prior master loop; rerun in final closeout before commit

cd apps/web && rm -rf .next && npm run build
# passed; route summary includes Middleware

cd apps/web && npm run typecheck && npx vitest run --config vitest.config.mts --testTimeout=10000
# 120 passed, 4 skipped

cd apps/web && npx vitest run --config vitest.config.mts middleware.test.ts --testTimeout=10000
# 6 passed after RED confirmed the public API base URL proxy risk
```

Current stop condition: rerun full closeout verification after documentation reconciliation, obtain fresh post-implementation review PASS, then final git/remote checks decide whether commit and push are safe.

## Final closeout scope warning

This is a Builder-only findings closure. It does not implement Daedalus order-flow profile state machines, does not add live order authority, and does not prove production/live-trading readiness. NautilusTrader adapter/live readiness still requires DataTester, ExecTester, reconciliation evidence, and Daedalus execution-boundary approval.
