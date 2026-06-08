# Nautilus Builder Handguard

**Review date:** 2026-06-08
**Purpose:** Runtime and review invariants for Nautilus Builder. These are hard boundaries, not suggestions.
**Current state:** REQUEST CHANGES for production/security readiness. Clean-route/Overview local UI closeout remains verified, but critical credential packaging/storage and runtime-safety findings are open. Production/live trading readiness is not claimed.

## 0. Current review gate — 2026-06-08 post-route standardization

**Gate verdict:** **REQUEST CHANGES** before production/security readiness. The clean-route/Overview UX closeout is verified, but the following guard violations are open and must be treated as blockers for any production or live-readiness claim.

### Immediate blocker guards

1. **Credential packaging guard:** Docker builds must never copy `.env.execution.local` or any `.env*` secret file into an image or remote build context. Current evidence: `Dockerfile.api:13-15`, missing `.dockerignore`, and a local untracked `.env.execution.local` with credential variable names. Remove the copy pattern, add `.dockerignore`, and rotate any real keys.
2. **Browser credential guard:** Builder UI must not collect raw venue credentials. Current evidence: `apps/web/components/config/CredentialSlotBootstrap.tsx:11-14`, `25-35`, `62-69`. Replace with backend-only secret references or a CLI/admin bootstrap.
3. **Paper/runtime credential guard:** Paper sessions must not require live venue credentials or construct live venue data/exec clients from browser-provided secrets. Current evidence: `packages/execution_lane/sessions.py:218-232`, `packages/execution_lane/adapter_config_builders.py:31-70`.
4. **Dev server exposure guard:** `nautilus-builder-api` must not start an unauthenticated mutating API on non-loopback hosts. Current evidence: `pyproject.toml:19-20`, `services/api/dev_server.py:39-44`, `services/api/app.py:57-125`.
5. **Rate-limit enforcement guard:** A configured limiter must be enforced by middleware/dependency before readiness claims. Current evidence: `services/api/fastapi_app.py:182-195` constructs a limiter but no route calls it.
6. **Audit attribution guard:** Mutations must persist actor/project attribution and must not silently drop audit failures. Current evidence: `packages/auth/audit_middleware.py:64-77`, `packages/postgres/migrations.py:199-210`, `services/api/fastapi_app.py:891-910`.
7. **Artifact readiness guard:** FastAPI startup/readiness must initialize and report an actual artifact store from env/factory before BacktestNode/promotion readiness claims. Current evidence: `services/api/fastapi_app.py:98-105`, `226`, `338`, `635`.
8. **LLM config persistence guard:** Postgres-backed config saves must preserve `_pg_config_repo`; do not reset it to `None` after loading. Current evidence: `services/api/fastapi_app.py:141-151`, `168-169`, `424-429`.
9. **Frontend action-ownership guard:** The web UI may request/observe backend plans; it must not be the authority constructing risk-approved order intents or runtime worker/session actions. Current evidence: `apps/web/components/config/ExecutionLaneFeaturePanel.tsx:137-160`, `325-372`, `539-552`.
10. **Safety scan guard:** `scripts/check_forbidden_authority.sh` must scan production directories by default rather than allowlisting `packages/`, `services/`, and `apps/web`.

### Current web-route guard

- Keep sidebar links as clean paths: `/`, `/builder`, `/backtests`, `/execution`, `/strategies`, `/pipeline`, `/results`, `/config`.
- Do not reintroduce `?tab=strategy`, `?tab=backtest`, or `?tab=execution` for primary navigation.
- Keep Overview as distinct summary/data-view content, not a duplicate Strategy Builder lane.

### Current positive guard evidence

- No direct production Builder `submit_order(` or authoritative `TradeAction(` construction was found in the focused source scan.
- `NEXT_PUBLIC_BUILDER_API_TOKEN` remains forbidden by policy and not used for browser token proxying.
- `aiogram`/Telegram and LangChain/LangGraph/EvoMap remain outside Builder runtime dependencies; keep them as Daedalus/advisory boundaries unless a separate design is approved.


## 1. Authority boundary — Builder never owns live order submission

Builder production code must not call `submit_order(`, construct authoritative `TradeAction(`, hold direct exchange execution credentials in browser/UI state, or directly couple to Daedalus runtime internals.

Required false/blocked values in Builder-owned production paths:

```python
execution_authority = False
may_submit_order = False
live_trading_authority = False
advisory_only = True
browser_credentials_allowed = False
credential_inputs_allowed = False
strategy_lane_coupled = False
```

Current enforcement surfaces:

- `packages/strategy_validation/policy.py` blocks `submit_order`, `modify_order`, `cancel_order`, `close_position`, `TradeAction`, and credential terms in StrategySpec inputs.
- `packages/backtest_runner/config_builder.py` rejects live credentials in backtest config.
- `packages/backtest_runner/contracts.py` uses `Literal[False]` for backtest execution authority and credential usage.
- `packages/execution_lane/models.py` rejects paper-mode live authority and requires multiple gates for any live authority fields.
- `packages/execution_lane/sessions.py` keeps paper session configs `execution_authority=False` and `may_submit_order=False`.

Guard: reject any PR that adds a Builder-side production `submit_order(` path or authoritative `TradeAction(` construction.

## 2. API auth and project-scope gate — Segment 4 closed

Every `/api/*` FastAPI route except health/build liveness endpoints must do all of the following:

1. Accept bearer authorization.
2. Call `require_context(authorization)`.
3. Return `401` when auth is absent/invalid.
4. Pass `UserProjectContext` into package/repository calls that read or mutate scoped data.
5. Return `403` or an empty scoped list for wrong-project access.

Segment 1 closed strategy list/approve/clone scope leaks in focused tests. Segment 4 replaced static auth tests with runtime missing-auth checks for every registered FastAPI `/api/*` route. No `/api/*` route is public in FastAPI unless a future product decision adds an explicit allowlist with tests.

Guard: no production-readiness claim until runtime tests prove missing-token and wrong-project requests fail for every protected `/api` route.

## 3. Production environment policy gate — Segment 2 closed

`packages/auth/policy.py` defines the required policy:

- `BUILDER_ENV` must be `local`, `staging`, or `production`.
- In `staging` or `production`, `BUILDER_API_TOKEN` must exist, be at least 32 chars, and not be a known dev token.
- `NEXT_PUBLIC_BUILDER_API_TOKEN` is forbidden in staging/production.
- CORS origins must not be empty or wildcard in staging/production.

Guard: `services/api/fastapi_app.py` calls `validate_builder_env()`, `validate_production_token()`, and `validate_cors_config()` during startup. Do not remove that startup gate or rely only on `_register_env_dev_token()`.

## 4. Strategy repository scope gate

All strategy repositories must preserve and enforce `user_id`/`project_id` scope for:

- save/create
- list
- detail
- update draft
- create version
- approve/update status
- clone

Guard: Postgres strategy storage must include scope columns or equivalent scoped ownership metadata. In-memory and Postgres repositories must have the same context semantics.

## 5. NautilusTrader evidence gate

Builder may produce and store:

- StrategySpec drafts and versions
- validation reports
- compile metadata/artifacts
- backtest jobs/results/manifests
- evidence refs and promotion gate decisions

Builder must not claim it produces adapter-compliance evidence unless an actual adapter suite produced it. For NT adapter readiness claims, require:

- DataTester evidence for claimed data adapter behavior.
- ExecTester evidence for claimed execution adapter behavior.
- Reconciliation reports for claimed live execution readiness.
- Adapter guide capability matrix for venue-specific behavior.

Guard: UI/docs must distinguish `passed_inferred` from artifact-backed evidence. Do not mark compile/replay/promotion as production-ready from lifecycle status alone.

## 6. TradingNode / LiveNode wording gate

- Python `nautilus_trader.live.node.TradingNode` examples in Builder are integration-specific/paper sandbox contracts.
- Rust-backed `nautilus_trader.live.LiveNode` is the current/future Rust v2 path for new Rust-backed PyO3 adapter work.
- Builder does not currently run Rust `LiveNode`.

Guard: reject docs that present Builder's Python TradingNode contract as universal Nautilus live production readiness.

## 7. Daedalus boundary gate

Daedalus is the execution authority and owns:

- approved-intent `TradeAction` generation/handling
- order submission surface
- `ExecutionReport` source of execution truth
- Telegram delivery runtime
- EvoMap/LangChain/LangGraph decision/advisory lanes
- custom adapter runtime evidence

Builder may reference Daedalus only through documented handoff/evidence contracts. Builder must not import or edit Daedalus internals from this repo.

Guard: no direct `Nautilus-Daedalus` runtime imports in Builder packages/services.

## 8. aiogram-dialog / Telegram gate

Builder must not add `aiogram` or `aiogram-dialog` dependencies. Telegram dialog/menu ownership remains in Daedalus (`nautilus_runtime/live/telegram_gateway/`). Builder may emit/record notification configuration contracts only after explicit design and tests.

Guard: reject Builder-side aiogram/aiogram-dialog runtime dependencies.

## 9. AI advisory gate

Builder AI output is advisory-only:

- Provider endpoint comes from operator env/config, never model output.
- LLM output must pass StrategySpec validation before acceptance.
- No AI output may auto-apply live strategy rules or execution authority.
- Prompt/audit persistence must redact secrets before production use.

Guard: treat all model output and user prompt text as untrusted input.

## 10. Postgres identifier gate

Every schema/table identifier interpolated into SQL must be validated with a strict identifier helper before use. Parameter binding protects values, not identifiers.

Guard: constructors and migrations must reject unsafe schema/table names. Do not interpolate operator-controlled identifiers raw.

Segment 3 status: closed for current Postgres repositories, migration entrypoints, seed helpers, and demo seed paths through `packages.postgres.identifiers`.

## 11. Fixture/demo evidence gate

Fixture and demo data are allowed only when explicitly labelled and disabled by default in production:

- `BUILDER_ALLOW_FIXTURE_FALLBACK` must remain off by default.
- `res_001` fallback must be fixture/dev-only.
- Demo compile hashes must not be presented as real artifact checksums.
- Seed scripts must not hide unexpected failures.

Guard: reject any PR that silently converts demo/fixture evidence into production evidence.

Segment 3 status: seed script save failures now propagate, and lifecycle-only compile evidence is represented as `passed_inferred` rather than artifact-backed `passed`.

## 12. Worker isolation gate

Native Nautilus runners must not run from the API event loop. They belong in backend worker processes or explicit CLI/operator paths.

Guard: `services/api/` must not directly start a native `TradingNode`; worker entrypoints own runtime lifecycle.

## 13. Verification gate before readiness claims

Minimum backend gate:

```bash
python3 -m compileall -q packages services tests scripts
python3 -m pytest tests/ -q --tb=line
```

Frontend readiness gate when UI claims change:

```bash
cd apps/web && npx tsc --noEmit
cd apps/web && npx vitest run
cd apps/web && npm run build
```

Runtime/live-readiness claims also require NT evidence refs (DataTester/ExecTester/reconciliation) and Daedalus execution-boundary confirmation.

## 14. Legacy/deprecation closure schedule

| Item | Status on 2026-06-08 | Deadline | Guard |
|---|---|---:|---|
| `storage_config.py` legacy schema alias | OPEN | 2026-07-01 | Remove after cutoff; no new callers. |
| `PostgresWorkflowRepository` alias | OPEN | 2026-07-01 | Prefer `SqliteWorkflowRepository`; remove alias after cutoff. |
| Backtest legacy hash derivation | OPEN | 2026-07-01 | Keep disabled by default; remove env escape after cutoff. |
| `allow_legacy_fixture_refs` | OPEN | 2026-07-01 | Strict evidence for non-dev promotions. |
| `res_001` fixture fallback | WATCH | 2026-07-01 | Production flag must stay off. |
| `NEXT_PUBLIC_BUILDER_API_TOKEN` local mode | CLOSED/WATCH | n/a | Browser-exposed Builder API tokens are forbidden; web proxy uses server-side `BUILDER_API_TOKEN` only when web env is explicitly local. |

## 15. Current production-scope watches

Do not claim production/live-trading readiness from this closeout. Merge-readiness is limited to the Builder-only dev-demo scope after final git/remote checks.

See `findings.md` for file/line evidence and concrete fixes.


## Segment 3 reconciliation — storage and evidence hardening

**Completed:** 2026-06-08

Implemented and verified Postgres identifier validation, indexed Postgres backtest evidence reads, lifecycle-only compile evidence status splitting, and demo seed failure propagation.

Verification evidence:

```bash
python3 -m pytest tests/postgres/test_identifier_safety.py tests/backtest_jobs/test_postgres_service.py tests/api/test_evidence_summary.py::test_backtested_strategy_has_compile_evidence tests/api/test_evidence_summary.py::test_compile_status_inferred_from_lifecycle_does_not_create_compile_audit tests/scripts/test_seed_builder_demo_data.py -q
# 15 passed

python3 -m pytest tests/postgres tests/api/test_evidence_summary.py tests/backtest_jobs tests/scripts/test_seed_builder_demo_data.py -q
# 101 passed

python3 -m compileall -q packages/postgres packages/backtest_jobs/postgres_service.py services/api/routes/evidence_summary.py scripts/seed_builder_demo_data.py tests/postgres/test_identifier_safety.py tests/backtest_jobs/test_postgres_service.py tests/scripts/test_seed_builder_demo_data.py tests/api/test_evidence_summary.py
# pass
```

Remaining work: final git/remote checks.


## Segment 4 reconciliation — runtime auth coverage

**Completed:** 2026-06-08

Implemented and verified runtime missing-auth coverage across the registered FastAPI `/api/*` route table. The route-auth test now fails on newly mounted untested API routes and on protected routes that do not return `401` without a bearer token. FastAPI catalog/profile/registry metadata routes now require auth.

Verification evidence:

```bash
python3 -m pytest tests/api/test_route_auth_scope.py::TestRouteAuthScope::test_every_registered_api_route_is_auth_tested tests/api/test_route_auth_scope.py::TestRouteAuthScope::test_protected_api_routes_reject_missing_auth_at_runtime -q
# 2 passed

python3 -m pytest tests/api/test_route_auth_scope.py tests/api/test_fastapi_app.py tests/api/test_production_safety.py tests/api/test_security_hardening.py tests/auth -q
# 91 passed, 1 skipped, 1 warning (Starlette/httpx deprecation from testclient)

python3 -m compileall -q services/api/fastapi_app.py tests/api/test_route_auth_scope.py
# pass
```

Remaining work: final git/remote checks.

## 16. Master reconciliation — catalog-backed Nautilus replay

`CATALOG_BACKED_REPLAY_SMOKE_MODE` / `catalog_backed_replay_smoke` must remain a smoke-only gate. It writes synthetic historical quote ticks into a catalog and exercises NautilusTrader BacktestNode replay wiring. It is **not full trading-production readiness**, and it does not satisfy DataTester, ExecTester, adapter reconciliation, or live execution evidence requirements.


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

At Segment 2 completion time, remaining blockers were H-04 runtime auth coverage plus medium storage/evidence and demo-hygiene findings.

## Master reconciliation — findings closure implementation

**Updated:** 2026-06-08

Master reconciliation verifies the Segment 1-4 closure plus follow-up review fixes as Builder-only dev-demo hardening. It does not claim production/live-trading readiness. The latest follow-up fixes include strictest-env durable audit-store enforcement, production Redis rate-limit startup enforcement, runtime `/health/backend` proxying, removal of build-time API rewrites, localhost-only local API compose exposure, and web/API-client token injection that requires explicit local env instead of treating unset env as local.

Fresh verification evidence recorded in this closeout cycle:

```bash
python3 -m compileall -q packages services tests scripts && python3 -m pytest tests/ -q --tb=line
# 954 passed, 1 skipped, 1 warning

python3 -m pytest tests/api/test_production_safety.py tests/api/test_fastapi_app.py::test_fastapi_workflow_routes_require_auth_and_deny_cross_project tests/api/test_fastapi_app.py::test_fastapi_demo_seed_uses_default_dev_token_scope tests/api/test_fastapi_app.py::test_fastapi_execution_lane_routes_filter_runtime_state_by_project tests/api/test_evidence_summary.py::test_evidence_summary_filters_backtest_jobs_by_project -q --tb=short
# 16 passed after strictest audit-store policy fix

bash scripts/check_forbidden_authority.sh && git diff --check
# passed in final closeout

cd apps/web && rm -rf .next && npm run build
# passed; route summary includes Middleware

cd apps/web && npm run typecheck && npx vitest run --config vitest.config.mts --testTimeout=10000
# 123 passed, 4 skipped

cd apps/web && npx vitest run --config vitest.config.mts middleware.test.ts --testTimeout=10000
# superseded by the targeted deployment-safety loop below

cd apps/web && npx vitest run --config vitest.config.mts middleware.test.ts lib/api.test.ts --testTimeout=10000
# 20 passed after RED confirmed runtime health proxying and explicit-local token injection

python3 -m pytest tests/integration/test_docker_compose_profiles.py tests/web/test_frontend_infrastructure.py -q
# 36 passed after RED confirmed localhost API binding, explicit web envs, and no build-time rewrites
```

Historical prior-closeout stop condition: full verification and post-implementation review had passed for that earlier branch. Current addendum stop condition is publication-only after clean git/remote checks; production/security readiness remains blocked until the guard violations in section 0 are fixed.

## Production/live-readiness warning

This closeout is scoped to Builder findings hardening and dev-demo verification. Live trading remains outside Builder authority. Any future production/live-trading claim still requires NautilusTrader DataTester, ExecTester, adapter reconciliation evidence, Daedalus execution-boundary confirmation, and manual operator approval.
