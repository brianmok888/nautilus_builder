# Nautilus Builder Handguard

**Review date:** 2026-06-08
**Purpose:** Runtime and review invariants for Nautilus Builder. These are hard boundaries, not suggestions.
**Current state:** CLOSED for the user-listed Builder security blockers; WATCH for production/live readiness. Segments 1-5 closed Docker credential packaging, browser/API credential entry, packaged API exposure, protected-route rate limiting, audit actor/project attribution, artifact readiness, LLM persistence, frontend runtime-action ownership, and safety-scan hardening. Production/live trading readiness is not claimed.

## 0. Current review gate — 2026-06-08 post-route standardization

**Gate verdict:** **CLOSED for the reviewed Builder-only blocker set; WATCH before any production/live-readiness claim.** The clean-route/Overview UX closeout is verified; Segment 3 closes artifact readiness and LLM persistence; Segment 4 closes frontend runtime-action ownership; Segment 5 closes safety-scan production-path coverage.

### Immediate blocker guards

1. **Credential packaging guard — CLOSED Segment 1:** Docker builds must never copy `.env.execution.local` or any `.env*` secret file into an image or remote build context. Current evidence: `Dockerfile.api` no longer copies env files and `.dockerignore` excludes `.env*`; rotate any real keys that existed before closure.
2. **Browser credential guard — CLOSED Segment 1:** Builder UI must not collect raw venue credentials. Current evidence: Settings no longer imports `CredentialSlotBootstrap`, the frontend API client no longer exposes `/api/execution-lane/credential-slots`, and HTTP credential-slot writes return `credential_slot_http_disabled`. Future secret provisioning must be backend-only or CLI/admin-only.
3. **Paper/runtime credential guard:** Paper sessions must not require live venue credentials or construct live venue data/exec clients from browser-provided secrets. Current evidence: `packages/execution_lane/sessions.py:218-232`, `packages/execution_lane/adapter_config_builders.py:31-70`.
4. **Dev server exposure guard — CLOSED Segment 2:** `nautilus-builder-api` must not start an unauthenticated mutating API on non-loopback hosts. Current evidence: the console script now targets `services.api.fastapi_cli:main`, and `services/api/dev_server.py` rejects non-loopback binds unless explicitly unsafe.
5. **Rate-limit enforcement guard — CLOSED Segment 2:** A configured limiter must be enforced by middleware/dependency before readiness claims. Current evidence: protected FastAPI `require_context()` calls now enforce `is_allowed()` after auth, Redis URL logs are redacted, and production Redis outage behavior fails closed.
6. **Audit attribution guard — CLOSED Segment 2:** Mutations must persist actor/project attribution. Current evidence: `AuthContextMiddleware` attaches valid bearer actor/project to request state and Postgres audit inserts include `project_id`. Successful mutations fail closed if audit persistence fails, while already-failed mutations keep their original error response.
7. **Artifact readiness guard — CLOSED Segment 3:** FastAPI startup/readiness initializes a default artifact store from env/factory before BacktestNode/promotion readiness claims. Current evidence: `create_fastapi_app()` calls `create_artifact_store()` when no store is injected, `create_artifact_store()` honors `BUILDER_ARTIFACT_ROOT`, and `/health/ready` reports factory errors as not ready.
8. **LLM config persistence guard — CLOSED Segment 3:** Postgres-backed config saves preserve `_pg_config_repo` after loading. Current evidence: `_pg_config_repo` is initialized before the Postgres branch and passed to `save_llm_config_payload()` when `_pg_conn` is configured.
9. **Frontend action-ownership guard — CLOSED Segment 4:** The web UI may request/observe backend plans; it must not be the authority constructing risk-approved order intents or runtime worker/session actions. Current evidence: `ExecutionLaneFeaturePanel` only registers profile visibility and fetches runtime plans; `apps/web/lib/api.ts` no longer exports command, worker, or paper-session action helpers.
10. **Safety scan guard — CLOSED Segment 5:** `scripts/check_forbidden_authority.sh` must scan production directories by default rather than allowlisting `packages/`, `services/`, and `apps/web`. Current evidence: the script scans `packages`, `services`, and `apps/web`, excludes frontend tests/specs by path, uses fixed-string grep, and allows only exact-line false positives.

### Current web-route guard

- Keep sidebar links as clean paths: `/`, `/builder`, `/backtests`, `/execution`, `/strategies`, `/pipeline`, `/results`, `/config`.
- Do not reintroduce `?tab=strategy`, `?tab=backtest`, or `?tab=execution` for primary navigation.
- Keep Overview as distinct summary/data-view content, not a duplicate Strategy Builder lane.

### Segment 1 verification evidence

```bash
python3 -m pytest tests/test_dockerfile_safety.py tests/api/test_fastapi_app.py::test_fastapi_execution_lane_credential_slot_api_rejects_browser_credentials tests/web/test_execution_lane_ui_contract.py -q
# 4 passed

cd apps/web && npm run test -- lib/api.test.ts components/config/ExecutionLaneFeaturePanel.test.tsx
# 2 files passed; 14 passed, 2 skipped
```

### Segment 2 verification evidence

```bash
python3 -m pytest tests/api/test_production_safety.py tests/api/test_route_auth_scope.py tests/api/test_fastapi_app.py tests/auth/test_redis_rate_limit.py tests/auth/test_redis_rate_limit_security.py tests/auth/test_audit_middleware.py tests/auth/test_audit_attribution.py tests/postgres/test_audit_event_hardening.py tests/api/test_security_hardening.py tests/auth/test_rate_limit.py tests/auth/test_token_context.py -q
# 117 passed, 1 skipped, 1 warning

python3 -m compileall -q services/api/fastapi_app.py services/api/dev_server.py services/api/fastapi_cli.py packages/auth/audit_middleware.py packages/auth/context_middleware.py packages/auth/redis_rate_limit.py packages/postgres/audit_event_repository.py packages/postgres/migrations.py packages/postgres/promotion_ledger_repository.py tests/api/test_production_safety.py tests/api/test_route_auth_scope.py tests/api/test_fastapi_app.py tests/auth/test_redis_rate_limit.py tests/auth/test_audit_middleware.py tests/auth/test_audit_attribution.py tests/auth/test_redis_rate_limit_security.py tests/postgres/test_audit_event_hardening.py
# pass
```

### Segment 3 verification evidence

```bash
python3 -m pytest tests/api/test_artifact_readiness_and_llm_config.py tests/artifact_store/test_factory_env.py tests/artifact_store/test_s3_artifact_store.py tests/api/test_fastapi_app.py tests/api/test_route_auth_scope.py tests/api/test_llm_config_routes.py -q
# 49 passed, 1 skipped, 1 warning

python3 -m compileall -q packages/artifact_store/factory.py services/api/fastapi_app.py tests/api/test_artifact_readiness_and_llm_config.py tests/artifact_store/test_factory_env.py
# pass

git diff --check
# pass
```

### Segment 4 verification evidence

```bash
cd apps/web && npm run test -- components/config/ExecutionLaneFeaturePanel.test.tsx lib/api.test.ts
# 14 passed, 2 skipped

cd apps/web && npm run typecheck
# pass

python3 -m pytest tests/web/test_execution_lane_ui_contract.py -q
# 1 passed

git diff --check
# pass
```

### Segment 5 verification evidence

```bash
python3 -m pytest tests/hygiene/test_repo_hygiene.py -q
# 11 passed

bash scripts/check_forbidden_authority.sh
# PASSED

git diff --check
# pass
```

### Final reconciliation verification evidence

```bash
python3 -m pytest tests/api/test_execution_lane_credentials_routes.py tests/api/test_execution_lane_tradingnode_routes.py::test_execution_lane_session_start_and_stop_routes_return_lifecycle tests/integration/test_headless_backend_runtime.py::test_pyproject_exposes_headless_backend_entrypoints tests/onboarding/test_docker_zero_config.py::TestDockerfiles::test_api_dockerfile_does_not_create_or_copy_local_credential_env_file tests/web/test_sectioned_operator_ui.py::test_execution_config_section_keeps_feature_flags_read_only_and_secret_free -q
# 6 passed

python3 -m compileall -q packages services tests scripts && python3 -m pytest tests/ -q --tb=line
# 979 passed, 1 skipped, 1 warning

cd apps/web && npm run typecheck
# pass

cd apps/web && npm test
# Test Files 33 passed, 1 skipped; Tests 131 passed, 4 skipped

cd apps/web && npm run build
# pass
```

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


## Segment 5 reconciliation — forbidden-authority safety scan

**Completed:** 2026-06-08

Implemented and verified production-path coverage for the forbidden-authority scan. The scan no longer allowlists production directories after matches; it searches `packages`, `services`, and `apps/web` by default, excludes frontend tests/specs, uses fixed-string matching for authority literals, and keeps false-positive exceptions to exact lines.

Verification evidence:

```bash
python3 -m pytest tests/hygiene/test_repo_hygiene.py -q
# 11 passed

bash scripts/check_forbidden_authority.sh
# PASSED

git diff --check
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


## Gap Closure v1 guards — 2026-06-11

New guards from the gap closure:

1. **Version consistency guard:** `packages/builder_metadata/version.py` is the single canonical source. `/health/build` and FastAPI `app.version` read from it. Tests fail on drift.

2. **CI gate guard:** `.github/workflows/ci.yml` runs backend/safety/frontend/docker jobs on every PR. PRs fail on forbidden authority, version drift, test failures.

3. **Readiness wording guard:** `tests/hygiene/test_readiness_wording.py` scans docs for unsafe live-readiness claims. `READINESS.md` provides the canonical readiness matrix.

4. **StrategySpec v2 guard:** v2 models enforce `execution_authority=False`. v1 still works. Migration is tested.

5. **Deterministic hash guard:** Compiler IR, risk contract, artifact bundle all produce deterministic SHA-256 hashes tested for reproducibility.

6. **Evidence guard:** Evidence refs require project scoping and hash verification. Verifier enforces hash length for artifact-backed evidence.

7. **Promotion gate guard:** Promotion requires typed evidence. Synthetic backtest cannot satisfy catalog requirement. Live candidate is always out of scope.

8. **OpenAPI contract guard:** Snapshot test detects API path drift. All `/api/*` routes require auth.

9. **Production policy guard:** Policy matrix tests verify token length, CORS, and env validation.

10. **Runtime event guard:** Event types are structured and queryable. No live execution or order submission events exist.


## Gap Closure v2 guards — 2026-06-11

New guards from the v2 gap closure:

1. **BuilderBuildInfo guard:** `/health/build` returns typed model with env-injected git/build metadata. Tests verify version, git_commit, build_time_utc fields.

2. **Readiness API guard:** GET `/api/readiness` returns machine-readable matrix. Live execution is always `out_of_scope`. Tests fail if this changes.

3. **Feature registry guard:** `feature_registry.py` defines canonical ND feature names. Unknown features fail validation.

4. **Authority rules guard:** `authority_rules.py` blocks forbidden output modes and authority fields in specs. Tests verify signal_preview_only passes, live_execution blocked.

5. **FullArtifactBundle guard:** `CompileArtifactManifest.execution_authority` is `Literal[False]`. Cannot be set to `True`.

6. **Evidence policy guard:** Promotion requires typed evidence sets. Synthetic backtest cannot satisfy catalog requirement. Live candidate always blocked.

7. **Object storage guard:** `LocalObjectStorage` rejects path traversal. Factory pattern isolates backend selection.

8. **Capabilities guard:** Builder has no live execution, order submission, or trade action capabilities. Operator cannot approve promotions.

9. **Audit guard:** Required event types include no live execution or order submission events.

10. **Metrics guard:** Metric names track validation, compile, backtest, evidence, promotion blocks. No live execution metrics.

11. **Docs consistency guard:** `scripts/check_docs_consistency.py` verifies README, READINESS.md, version strings, and Builder boundary mentions.

12. **Local CI parity guard:** `scripts/verify_all.sh` mirrors CI checks locally.


## Gap Closure v3 guards — 2026-06-11

New guards from the v3 closure:

1. **Legacy removal guard:** `tests/hygiene/test_legacy_removal.py` verifies PostgresWorkflowRepository alias, legacy hash derivation, allow_legacy_fixture_refs, and res_001 fixture fallback are all removed from production code.

2. **Prompt redaction guard:** `tests/ai_builder/test_prompt_redaction.py` verifies secrets are redacted from prompts before audit storage, and prompt hashes are preserved for forensic traceability.

3. **Frontend API consistency guard:** `apiClient.ts` is deprecated. All production components use the canonical `apiFetch` from `api.ts`. Direct `fetch()` calls exist only for public endpoints (`/health`) with documented justification.

4. **Readiness wording guard:** `tests/hygiene/test_readiness_wording_v3.py` scans docs for unsafe live-readiness phrases. Forbidden unless in negative context.

5. **Verification harness guard:** `scripts/verify_builder.py` provides one-command verification with local/staging/production-check profiles.

6. **Deprecation inventory guard:** `docs/deprecations/deprecation-inventory.md` tracks all deprecations. Currently empty (all removed).

### Legacy closure complete

All legacy items listed in handguard.md §14 have been removed:
- `storage_config.py` deprecation comment — removed
- `PostgresWorkflowRepository` alias — removed
- Backtest legacy hash derivation — removed
- `allow_legacy_fixture_refs` — removed
- `res_001` fixture fallback — removed
- `USE_LEGACY_COMPILE_HASH` env escape — removed
- `BUILDER_ALLOW_FIXTURE_FALLBACK` env — removed
- Legacy warning suppression in pyproject.toml — removed
