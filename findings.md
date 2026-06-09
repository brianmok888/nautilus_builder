# Nautilus Builder Deep Review Findings

**Review date:** 2026-06-08
**Scope:** Current repository (`packages/`, `services/`, `apps/web/`, `tests/`, `scripts/`, `doc/`, `docs/`) plus current uncommitted diff.
**Reference repo:** `/home/mok/projects/Nautilus-Daedalus`
**Method:** `$superpowers:code-review`, `nt-review` primary, `nt-architect`/`nt-adapters`/`nt-live`/`nt-testing` supporting, aiogram-dialog negative-inventory lens, official NautilusTrader/EvoMap/LangChain/LangGraph references, static grep, manual route probes, focused tests.

## Executive summary

**Final recommendation:** **REQUEST CHANGES** for production/security readiness. Segments 1-4 close credential/package safety, packaged API exposure, rate-limit enforcement, audit attribution, artifact readiness, LLM persistence, and frontend runtime-action ownership; safety-scan hardening remains open.
**Architectural status:** **BLOCK** for production/security readiness; **WATCH** for local dev-demo only until the safety-scan finding is closed.
**Production/live-readiness status:** **OUT OF SCOPE / WATCH** — this does not grant live execution authority, adapter compliance, or production trading readiness.

## Current deep review addendum — 2026-06-08 post-route standardization

**Recommendation:** **REQUEST CHANGES** before any production/security readiness claim. The previous one-line Backtest hash styling and clean-route UI closeouts remain verified; Segments 1-4 close credential/API/rate-limit/audit-attribution, artifact-readiness/LLM-persistence, and frontend runtime-action ownership blockers, while safety-scan hardening remains open.

### Current top-priority findings


### Segment 1 closure — credential/package safety (2026-06-08)

**Status:** CLOSED for Docker credential packaging and browser/API credential entry. Segment 2 also closes packaged API exposure, protected-route rate-limit enforcement, Redis credential redaction with production fail-closed behavior, and authenticated audit actor/project attribution. Segment 3 closes artifact readiness and LLM persistence; Segment 4 closes frontend runtime-action ownership. Production/security readiness remains **REQUEST CHANGES** because the safety-scan blocker still needs closure.

**Evidence:**

```bash
python3 -m pytest tests/test_dockerfile_safety.py tests/api/test_fastapi_app.py::test_fastapi_execution_lane_credential_slot_api_rejects_browser_credentials tests/web/test_execution_lane_ui_contract.py -q
# 4 passed

cd apps/web && npm run test -- lib/api.test.ts components/config/ExecutionLaneFeaturePanel.test.tsx
# 2 files passed; 14 passed, 2 skipped
```

**Changes:** `.dockerignore` now excludes `.env*` and local state, `Dockerfile.api` no longer copies `.env.execution.local`, Settings no longer mounts `CredentialSlotBootstrap`, the frontend API client no longer exposes credential-slot posting, and the FastAPI credential-slot route returns `credential_slot_http_disabled` without writing `.env.execution.local`.

### Segment 2 closure — API exposure, rate limits, and audit attribution (2026-06-08)

**Status:** CLOSED for packaged API exposure, protected-route rate-limit enforcement, Redis credential redaction/production fail-closed behavior, and authenticated audit actor/project attribution. Audit-write failures now fail closed for successful mutations, preserve failed mutation responses, and Postgres insert failures propagate for deterministic handling.

**Evidence:**

```bash
python3 -m pytest tests/api/test_production_safety.py tests/api/test_route_auth_scope.py tests/api/test_fastapi_app.py tests/auth/test_redis_rate_limit.py tests/auth/test_redis_rate_limit_security.py tests/auth/test_audit_middleware.py tests/auth/test_audit_attribution.py tests/postgres/test_audit_event_hardening.py tests/api/test_security_hardening.py tests/auth/test_rate_limit.py tests/auth/test_token_context.py -q
# 117 passed, 1 skipped, 1 warning

python3 -m compileall -q services/api/fastapi_app.py services/api/dev_server.py services/api/fastapi_cli.py packages/auth/audit_middleware.py packages/auth/context_middleware.py packages/auth/redis_rate_limit.py packages/postgres/audit_event_repository.py packages/postgres/migrations.py packages/postgres/promotion_ledger_repository.py tests/api/test_production_safety.py tests/api/test_route_auth_scope.py tests/api/test_fastapi_app.py tests/auth/test_redis_rate_limit.py tests/auth/test_audit_middleware.py tests/auth/test_audit_attribution.py tests/auth/test_redis_rate_limit_security.py tests/postgres/test_audit_event_hardening.py
# pass
```

**Changes:** `nautilus-builder-api` now starts `services.api.fastapi_cli:main`, the dependency-free dev server rejects non-loopback hosts unless explicitly unsafe, protected FastAPI routes enforce the configured limiter after bearer auth, Redis limiter warnings redact credentials and fail closed in production mode, `AuthContextMiddleware` attaches actor/project to request state, and Postgres audit inserts include `project_id`.

### Segment 3 closure — artifact readiness and LLM persistence (2026-06-08)

**Status:** CLOSED for FastAPI artifact-store startup/readiness wiring and Postgres-backed LLM config persistence. Production/security readiness remains **REQUEST CHANGES** because the safety-scan blocker still needs closure.

**Evidence:**

```bash
python3 -m pytest tests/api/test_artifact_readiness_and_llm_config.py tests/artifact_store/test_factory_env.py tests/artifact_store/test_s3_artifact_store.py tests/api/test_fastapi_app.py tests/api/test_route_auth_scope.py tests/api/test_llm_config_routes.py -q
# 49 passed, 1 skipped, 1 warning

python3 -m compileall -q packages/artifact_store/factory.py services/api/fastapi_app.py tests/api/test_artifact_readiness_and_llm_config.py tests/artifact_store/test_factory_env.py
# pass

git diff --check
# pass
```

**Changes:** `create_artifact_store()` now honors `BUILDER_ARTIFACT_ROOT` for the local backend, FastAPI initializes a default artifact store from the factory when none is injected, `/health/ready` reports artifact-store factory errors instead of unconditional readiness, and `_pg_config_repo` is preserved so `POST /api/config/llm` persists through the Postgres config repository.

### Segment 4 closure — frontend runtime-action ownership (2026-06-08)

**Status:** CLOSED for browser-owned execution-lane command/risk/worker/session action construction. Production/security readiness remains **REQUEST CHANGES** because the safety-scan blocker still needs closure.

**Evidence:**

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

**Changes:** `ExecutionLaneFeaturePanel` now registers backend-owned paper profile visibility and fetches runtime plans only. It no longer renders command queue, backend worker, or paper-session lifecycle controls; it no longer constructs `order_intent` or `risk_decision`; and `apps/web/lib/api.ts` no longer exports execution-lane command, worker, or session action helpers.

#### C-01 — Docker API image can include local exchange credentials

- **Status:** CLOSED in Segment 1 (2026-06-08)
- **Severity:** Previously CRITICAL
- **Files:** `Dockerfile.api:13-15`, `.gitignore:1-6`; missing `.dockerignore`; local untracked `.env.execution.local:1-2` was present with Binance credential variable names (values redacted, not copied into this report).
- **Closure:** `Dockerfile.api` no longer touches or copies `.env.execution.local`/`.env.local`, and `.dockerignore` excludes `.env*`, `.git`, caches, local DB/artifact folders, and build outputs. Operators should still rotate any real keys that may have been present before this closure.

#### C-02 — Builder accepts browser-entered venue credentials and stores raw values

- **Status:** CLOSED for browser/API entry in Segment 1 (2026-06-08); backend-only secret provisioning remains a future design seam.
- **Severity:** Previously CRITICAL
- **Files:** `apps/web/app/config/page.tsx:3-17`, `apps/web/components/config/CredentialSlotBootstrap.tsx:11-14`, `25-35`, `47-50`, `62-69`; `services/api/fastapi_app.py:431-444`; `packages/execution_lane/credentials.py:124-151`; `packages/execution_lane/sessions.py:218-232`; `packages/execution_lane/adapter_config_builders.py:31-70`.
- **Closure:** Settings no longer mounts credential bootstrap UI, the Execution Lane panel has no raw credential inputs, the frontend API client no longer posts credential slots, and the FastAPI credential-slot route returns `credential_slot_http_disabled` without persisting submitted values. Future secret provisioning must be backend-only or CLI/admin-only, separately designed and tested.

#### H-01 — Packaged `nautilus-builder-api` starts an unauthenticated dev server

- **Status:** CLOSED in Segment 2 (2026-06-08)
- **Severity:** Previously HIGH
- **Files:** `pyproject.toml:19-20`; `services/api/dev_server.py`; `services/api/fastapi_cli.py`; `services/api/app.py:57-125`.
- **Closure:** The installed console script now points to authenticated FastAPI via `services.api.fastapi_cli:main`. The dependency-free dev server remains available only as a local development helper and rejects non-loopback host binding unless `--unsafe-allow-non-loopback` is explicit.

#### H-02 — Rate limiting is configured but not enforced

- **Status:** CLOSED in Segment 2 (2026-06-08)
- **Severity:** Previously HIGH
- **Files:** `services/api/fastapi_app.py`; `packages/auth/redis_rate_limit.py`; `docker-compose.production.yml:69-70`.
- **Closure:** Protected FastAPI route handlers now enforce the configured limiter through `require_context()` after bearer auth. Redis limiter warnings redact credential-bearing URLs, and production Redis outage behavior fails closed instead of allowing traffic open.

#### H-03 — Mutation audit events are not attributable and may fail silently

- **Status:** CLOSED in Segment 2 (2026-06-08)
- **Severity:** Previously HIGH
- **Files:** `packages/auth/audit_middleware.py`; `packages/postgres/migrations.py:199-210`; `services/api/fastapi_app.py`.
- **Closure:** `AuthContextMiddleware` attaches authenticated `actor_id`/`project_id`/role to request state for valid bearer tokens, and the Postgres audit writer now persists `project_id`. Audit-write failures now fail closed for successful mutations, preserve failed mutation responses, and Postgres insert failures propagate for deterministic handling.

#### H-04 — Frontend can construct execution-lane order-intent/worker actions

- **Status:** CLOSED in Segment 4 (2026-06-08)
- **Severity:** Previously HIGH
- **Files:** `apps/web/components/config/ExecutionLaneFeaturePanel.tsx:137-160`, `325-350`, `362-372`, `539-552`.
- **Issue:** The browser constructs `order_intent` and an `approved` risk decision, queues the command, runs the backend worker once, and starts/stops paper sessions.
- **Risk:** Backend checks keep `may_submit_order=false` today, but this weakens the architectural rule that the UI is display/advisory only and should not own runtime-action composition.
- **Closure:** The web panel and API client now expose profile/runtime-plan request/observe behavior only. Browser code no longer constructs command/risk payloads or calls worker/session action endpoints.

#### M-01 — Artifact-store env/factory is not wired into FastAPI startup

- **Status:** CLOSED in Segment 3 (2026-06-08)
- **Severity:** Previously MEDIUM
- **Files:** `services/api/fastapi_app.py:98-105`, `226`, `338`, `635`; `packages/artifact_store/factory.py:24-45`; `services/api/routes/backtest_execution.py:193-198`; `docs/verification/local-verification-checklist.md:30`.
- **Issue:** `create_fastapi_app()` accepts `artifact_store` but does not create one from `BUILDER_ARTIFACT_ROOT`/`BUILDER_ARTIFACT_BACKEND`; `/health/ready` still reports `artifact_store: ok`.
- **Risk:** Local BacktestNode runs and strict promotion can fail with `artifact store is required` even when runbooks export artifact env variables.
- **Closure:** FastAPI now builds the artifact store from the factory during app startup when one is not injected, the local factory honors `BUILDER_ARTIFACT_ROOT`, and readiness reports factory failure as `ready=false`.

#### M-02 — Postgres LLM config saves do not persist after startup

- **Status:** CLOSED in Segment 3 (2026-06-08)
- **Severity:** Previously MEDIUM
- **Files:** `services/api/fastapi_app.py:141-151`, `168-169`, `424-429`; `services/api/routes/llm_config.py:21-23`.
- **Issue:** `_pg_config_repo` is created and used to load config, then reset to `None`, so `save_llm_config_payload(..., pg_config_repo=_pg_config_repo if _pg_conn else None)` never persists saves.
- **Risk:** UI says config saved but restart can revert to old/default config.
- **Closure:** `_pg_config_repo` is initialized before the Postgres branch and no longer reset after startup, so LLM config saves call `PostgresConfigRepository.set("llm_config", ...)` when Postgres is configured.

#### M-03 — Direct frontend fetches bypass the canonical API client

- **Severity:** MEDIUM
- **Files:** `apps/web/components/ai-builder/AiStrategyCopilot.tsx:29-35`, `134-137`; `apps/web/hooks/useHealthCheck.ts:24`; `apps/web/lib/apiClient.ts:25-69`; `apps/web/lib/api.ts:130-163`.
- **Issue:** Some UI code bypasses `lib/api.ts`, losing central auth/proxy/error behavior; `/api/adapters` auth errors can become non-array state and later crash `.map()`.
- **Risk:** Inconsistent local/prod behavior and poor UX under API auth/config errors.
- **Fix:** Route all API calls through `apiFetch` helpers and remove or wrap the older `apiClient.ts` module.

#### M-04 — Forbidden-authority scan allowlists production code directories

- **Severity:** MEDIUM
- **Files:** `scripts/check_forbidden_authority.sh:21-38`.
- **Issue:** The safety scan allowlists `packages/`, `services/`, and `apps/web/`, so it would miss future forbidden authority in production code.
- **Risk:** A green safety scan can provide false confidence.
- **Fix:** Invert the scan: search production code by default, allow only policy/docs/tests/negative literals, and keep an explicit false-positive allowlist.

### Web UI / UX status

- **Closed:** Overview and Strategy Builder no longer link to the same content. `Overview` uses `/` and `BuilderOverview`; Strategy Builder uses `/builder`; Backtest and Execution use `/backtests` and `/execution`.
- **Closed:** The `?tab=` route style is gone from `apps/web` source in this review scan.
- **Closed/WATCH:** Execution Lane controls now expose backend-owned profile/runtime-plan request-observe behavior only; continue to prefer “Paper / reviewed runtime gate” wording over any production/live-readiness implication.
- **WATCH:** Settings should not present credential bootstrap as normal web UX. Remove or isolate it behind a backend-only local operator path.

### Inventory-first semantic legacy/deprecation update

| Item | Current status | Evidence / closure action |
|---|---|---|
| `storage_config.py` legacy alias | **OPEN** | `packages/workflow_spine/storage_config.py:1-3`; keep 2026-07-01 removal deadline. |
| `PostgresWorkflowRepository` alias | **OPEN** | `packages/workflow_spine/postgres_repository.py:213-219`, `packages/workflow_spine/__init__.py:28-45`; remove after cutoff. |
| Backtest legacy hash derivation | **OPEN** | `services/api/routes/backtest_jobs.py:267-275`; keep disabled by default and remove env escape after cutoff. |
| `allow_legacy_fixture_refs` | **OPEN/WATCH** | `services/api/routes/promotions.py:22-34`, `pyproject.toml:36`; strict mode remains required for production. |
| `res_001` fixture fallback | **WATCH** | `services/api/routes/workflow_results.py:23-24`; flag-gated, keep production off. |
| `NEXT_PUBLIC_BUILDER_API_TOKEN` | **CLOSED/WATCH** | `packages/auth/policy.py:67-71`, `apps/web/middleware.ts:31-59`; reject browser-token reintroduction. |
| aiogram / Telegram | **CLOSED for Builder runtime** | No Builder dependency found; keep Telegram under Daedalus boundary. |
| LangChain/LangGraph/EvoMap | **CLOSED for Builder runtime** | No Builder dependency found; keep these as Daedalus/advisory references unless separately designed. |
| Query-tab routes | **CLOSED** | Source grep returned no `?tab=` / tab query references under `apps/web`. |

### Positive validation during this review

- No direct production Builder `submit_order(` call or authoritative `TradeAction(` construction was found in the focused source scan.
- `apps/web` safety tests referenced by the frontend review passed in the subagent lane (`middleware.test.ts`, `lib/api.test.ts`, `safety-contract.test.tsx`: 23 passed).
- Builder `pyproject.toml` still pins `nautilus_trader==1.227.0`; the local Daedalus reference currently pins `1.228.0`, so NT compatibility must be reviewed before any adapter/live-readiness claim.
- Official NautilusTrader and AI reference URLs were reachable during review; they remain authoritative for adapter/test/live/advisory boundaries.


The Builder/Daedalus/NautilusTrader execution boundary remains directionally correct: no Builder production path was found that directly calls `submit_order(` or constructs authoritative `TradeAction(`. The historical risk was not live order authority creep; it was cross-project data exposure/mutation and stale review artifacts that previously claimed `APPROVE` despite blockers.

## Current closure snapshot — post-review fixes

**Updated:** 2026-06-08

The Segment 1-4 closure and follow-up review fixes now cover:

- strategy list/detail/approve/clone project scoping;
- production startup token/CORS enforcement using the strictest configured `BUILDER_ENV`/`APP_ENV`;
- rejection of `BUILDER_DEV_AUTH_TOKEN` outside local mode;
- runtime missing-auth coverage for every registered FastAPI `/api/*` route;
- context-scoped `/api/results` listing and workflow result reads;
- context-scoped evidence-summary backtest jobs so same-version jobs from other projects cannot upgrade compile/replay evidence;
- execution-lane status, runtime-plan, profile, command, worker, and session routes scoped to bearer project;
- local-only Next middleware token injection and no server token in staging/production web compose services;
- demo seeding under the configured dev user/project scope;
- Postgres identifier validation before dynamic SQL construction.

Fresh verification evidence:

```bash
python3 -m compileall -q packages services tests scripts && python3 -m pytest tests/ -q --tb=line
# 954 passed, 1 skipped, 1 warning

bash scripts/check_forbidden_authority.sh && git diff --check
# passed

cd apps/web && rm -rf .next && npm run build
# passed; route summary includes Middleware

cd apps/web && npm run typecheck && npx vitest run --config vitest.config.mts --testTimeout=10000
# 123 passed, 4 skipped
```

Current stop condition for this addendum: focused review verification is green for publishing the review artifact after final git/remote checks, but production/security readiness remains **REQUEST CHANGES** until the blocker list above is fixed.

## Historical severity summary — prior Segment 1-4 closure

The table and detailed findings below this heading are retained as prior closure history. The **current** review verdict and priorities are the 2026-06-08 post-route-standardization addendum above.

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
- **Segment status:** **CLOSED** by Segment 1. Runtime tests now require bearer auth and project filtering.

### H-02 — Strategy approve/clone routes can mutate or copy another project’s strategy

- **Files:**
  - `services/api/fastapi_app.py:541-559`
  - `packages/strategy_spec/repository.py:144-177`
  - `packages/postgres/strategy_repository.py:147-197`
- **Evidence:** `approve_strategy()` and `clone_strategy()` authenticate a token but discard `context`; repository `update_status()`, `approve_strategy()`, and `clone_strategy()` do not scope-check. Postgres variants also ignore context and table rows do not include scope columns in the returned/listed records.
- **Manual probe:** A beta token successfully approved an alpha-owned `strategy_001`; beta clone also returned `201` and created `strategy_002` outside the original scope payload.
- **Risk:** Unauthorized promotion/lifecycle mutation and cross-project copying of strategy specs.
- **Fix:** Add context parameters to repository mutation methods, call `_assert_scope()`/SQL project predicates before mutation, and preserve scope on cloned strategies. Add cross-project negative tests for approve, clone, update-status, Postgres strategy repository paths.
- **Segment status:** **CLOSED** by Segment 1. In-memory and Postgres strategy repository paths now preserve and enforce user/project scope.

### H-03 — Production auth policy functions exist but FastAPI startup does not enforce them

- **Files:**
  - `packages/auth/policy.py:32-86`
  - `services/api/fastapi_app.py:161-164`, `services/api/fastapi_app.py:680-696`
  - `tests/api/test_production_safety.py:23-31`
- **Evidence:** `validate_builder_env()`, `validate_production_token()`, and `validate_cors_config()` enforce the stronger policy in isolation, but `create_fastapi_app()` does not import/call them. `_register_env_dev_token()` only rejects a small known-dev-token set in production. Existing tests accept `my-secret-prod-key-2026` in production, which is shorter than the 32-character policy requirement.
- **Manual probe:** With `APP_ENV=production`, a durable AI audit SQLite path, and `BUILDER_API_TOKEN=my-secret-prod-key-2026`, FastAPI startup succeeded.
- **Risk:** Production deployments can start with short or public tokens and invalid CORS unless another launcher performs validation.
- **Fix:** Call the policy functions during FastAPI app creation before token registration and CORS middleware setup. Update production tests to require 32+ chars, forbid `NEXT_PUBLIC_BUILDER_API_TOKEN`, reject wildcard/empty CORS in staging/production, and verify startup failure.
- **Segment status:** **CLOSED** by Segment 2 plus follow-up review fix. Startup now applies strictest configured environment and rejects `BUILDER_DEV_AUTH_TOKEN` outside local mode.

### H-04 — Static auth route test gives false confidence

- **Files:**
  - `tests/api/test_route_auth_scope.py:24-71`
  - `services/api/fastapi_app.py:234-252`, `services/api/fastapi_app.py:498-511`
- **Evidence:** The test only checks for an `authorization` parameter or a textual `require_context` occurrence; routes such as adapters, instruments, backtest profile validation, strategy registry external, and strategy list have an auth parameter but do not validate it.
- **Risk:** Future public routes can pass tests while bypassing auth.
- **Fix:** Replace the static source scan with runtime route tests that call each `/api` endpoint without auth and expect `401` unless explicitly allowlisted. Keep health endpoints public only.
- **Segment 4 status:** **CLOSED**. `tests/api/test_route_auth_scope.py` now exercises the registered FastAPI route table at runtime, verifies every `/api/*` route is covered, and expects missing auth to return `401`. The previously public FastAPI catalog/profile/registry routes now call `require_context()`.

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
- **Segment 3 status:** **CLOSED**. `packages.postgres.identifiers` now validates schema/table identifiers for Postgres repositories, migration entrypoints, default seed helpers, and demo seed paths. Covered by `tests/postgres/test_identifier_safety.py`.

### M-02 — `PostgresBacktestJobService.list_jobs_for_strategy()` scans all jobs

- **Files:**
  - `packages/backtest_jobs/postgres_service.py:136-142`
  - `packages/postgres/backtest_job_repository.py:183-190`
- **Evidence:** The repository already has `list_by_strategy_version()`, but the service refreshes all jobs and filters in memory.
- **Risk:** Performance and data-blast-radius issue as job volume grows; unnecessary full-table reads during evidence-summary calls.
- **Fix:** Delegate directly to `self._repo.list_by_strategy_version(strategy_version_id)` and scope by `UserProjectContext` when evidence summary is scoped.
- **Segment 3 status:** **CLOSED for query path**. `PostgresBacktestJobService.list_jobs_for_strategy()` now calls `list_by_strategy_version()` directly and refreshes only returned jobs into cache. Covered by `tests/backtest_jobs/test_postgres_service.py`.

### M-03 — Evidence summary can overstate compile evidence

- **Files:**
  - `services/api/routes/evidence_summary.py:59-67`, `services/api/routes/evidence_summary.py:110-115`
  - `packages/backtest_jobs/models.py:31-33`
  - `scripts/seed_demo_evidence.py:33-36`
- **Evidence:** If strategy status is `backtested`, `approved`, or `execution_ready`, compile status becomes `passed` even without a compile hash. `BacktestJob.compile_hash` accepts any string, and demo seed values use `sha256:demo_*` strings rather than 64-hex digests.
- **Risk:** UI can present implied compile evidence as equivalent to artifact-backed compile evidence.
- **Fix:** Split statuses: `passed_with_artifact`, `passed_inferred`, `missing`; validate production compile hashes as 64-hex or store `hash_scheme` explicitly. Keep demo hashes labelled `fixture_dev_only`/`demo_only`.
- **Segment 3 status:** **PARTIAL / WATCH**. Lifecycle-only compile success now reports `passed_inferred` and does not create compiled audit events. Artifact-hash strictness remains a future hardening item if non-demo compile hashes become production promotion evidence.

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
- **Segment 3 status:** **CLOSED**. The seed script no longer catches broad `Exception`; unexpected save failures propagate. It also reuses the canonical demo `StrategySpec` factory to avoid stale schema construction.

### L-02 — Stale review artifacts previously claimed all findings were fixed

- **Files:** `structure.md`, `findings.md`, `handguard.md`
- **Risk:** Operators may treat stale `APPROVE` text as current despite active blockers.
- **Fix:** This update replaces stale approve language with a dated 2026-06-08 REQUEST-CHANGES report.

### L-03 — Current changed diff lacks Postgres-focused evidence summary tests

- **Files:** `tests/api/test_evidence_summary.py`, `packages/backtest_jobs/postgres_service.py`
- **Risk:** Public method behavior is covered for in-memory service but not for the Postgres service/repository path.
- **Fix:** Add a repository mock or lightweight integration test proving `PostgresBacktestJobService.list_jobs_for_strategy()` delegates to `list_by_strategy_version()` and preserves ordering/scope.
- **Segment 3 status:** **CLOSED** by `tests/backtest_jobs/test_postgres_service.py`.

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
| `NEXT_PUBLIC_BUILDER_API_TOKEN` | **CLOSED/WATCH** | `apps/web/lib/api.ts`, `apps/web/middleware.ts`, compose tests, `.env.production.example` forbid browser-exposed Builder API tokens. Runtime proxy/token tests now require explicit local web env, no build-time rewrites, and no staging/production web `BUILDER_API_TOKEN`. | Web `/api/*` token injection is local-only and explicit; reject browser-token reintroduction and reject staging/prod token proxy defaults. |
| `aiogram` / `telegram` | **FALSE POSITIVE for Builder runtime** | No Builder dependency in `pyproject.toml`; docs reference Daedalus Telegram boundary. | Keep as Daedalus-only. Reject Builder aiogram dependency. |
| `langchain` / `langgraph` / `evomap` | **FALSE POSITIVE for Builder runtime** | No Builder dependency in `pyproject.toml`; Daedalus owns these AI lanes. | Keep Builder AI provider advisory-only; do not couple to Daedalus AI runtimes. |
| `fixture` / `fallback` | **WATCH** | Many intentional fixture/dev paths in backtest and workflow results. | Ensure every fixture path is labelled dev/test only and disabled by default in production. |

## NautilusTrader / Daedalus alignment notes

- Builder pins `nautilus_trader==1.227.0`; the local Daedalus reference pins `1.228.0`. Treat this drift as a required compatibility review item before claiming adapter/live-readiness alignment.
- Official NT adapter docs define layered Rust core + Python integration layers and require DataTester/ExecTester evidence for adapter readiness. Builder currently gates on evidence refs but should not claim it produces those adapter test artifacts.
- Official NT Data Testing Spec notes legacy Python `TradingNode` examples but prefers Rust-backed `LiveNode` for new Rust/PyO3 adapters. Builder docs should retain the `python_live_integration_specific` label for TradingNode contracts.
- Daedalus `AGENTS.md` and README state Telegram is downstream-only, TradeAction is approved intent rather than execution evidence, and ExecutionReport is the source for submitted/filled/rejected/canceled wording. Builder should mirror this boundary.

## Current diff inclusion assessment

**Historical prior-closeout inclusion assessment, retained for context only.** The earlier findings-closure diff did not introduce Builder order authority or Daedalus coupling and closed the listed Segment 3/4 items. The current 2026-06-08 addendum supersedes any merge-ready implication: production/security readiness is **REQUEST CHANGES**, and git/remote checks only decide whether this review artifact can be published.

## Verification evidence

```bash
python3 -m compileall -q packages services tests scripts && python3 -m pytest tests/ -q --tb=line
# 954 passed, 1 skipped, 1 warning

python3 -m pytest tests/api/test_production_safety.py tests/api/test_fastapi_app.py::test_fastapi_workflow_routes_require_auth_and_deny_cross_project tests/api/test_fastapi_app.py::test_fastapi_demo_seed_uses_default_dev_token_scope tests/api/test_fastapi_app.py::test_fastapi_execution_lane_routes_filter_runtime_state_by_project tests/api/test_evidence_summary.py::test_evidence_summary_filters_backtest_jobs_by_project -q --tb=short
# 16 passed after strictest audit-store policy fix

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

Former H-01/H-02/H-03 manual probes are now represented by regression tests and segment evidence below.

## Prior review verdict before Segment 1-4 closure

- **code-reviewer recommendation:** REQUEST CHANGES
- **architect status:** BLOCK
- **final recommendation:** REQUEST CHANGES

The Segment 1-4 implementation, master reconciliation, and final closeout verification below close this prior verdict for Builder-only dev-demo scope. Final git/remote checks remain.

Do not make production/live-readiness claims from this closeout. Merge-readiness is limited to Builder-only dev-demo scope after final git/remote checks pass.

## Master reconciliation — catalog-backed Nautilus replay

`catalog_backed_replay_smoke` remains recorded as a catalog-backed Nautilus replay smoke: it uses synthetic historical quote ticks and a no-order subscribe strategy to prove BacktestNode wiring. This is **not full trading-production readiness** and must not be used as adapter/live compliance evidence.


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

At Segment 2 completion time, remaining blockers were H-04 runtime auth coverage and Segment 3 storage/evidence verification.


## Segment 3 reconciliation — storage and evidence hardening

**Completed:** 2026-06-08

Implemented and verified the storage/evidence closure segment. Unsafe Postgres schema/table identifiers are rejected before SQL construction in repository constructors, migrations, seed helpers, and demo seed paths. Postgres backtest evidence reads now use the repository's strategy-version query rather than scanning all jobs. Compile evidence inferred only from lifecycle status now reports `passed_inferred`; artifact-backed jobs remain `passed`. Demo strategy seeding now reuses the canonical demo spec factory and propagates unexpected save failures.

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

Replaced the static route auth confidence test with runtime missing-auth coverage for every registered FastAPI `/api/*` route. The matrix test now fails on any unaccounted `/api/*` route and verifies missing bearer auth returns `401` before payload-specific behavior. The FastAPI adapters, instruments, data availability, backtest profile validation, and external strategy registry routes now require bearer auth.

Verification evidence:

```bash
python3 -m pytest tests/api/test_route_auth_scope.py::TestRouteAuthScope::test_every_registered_api_route_is_auth_tested tests/api/test_route_auth_scope.py::TestRouteAuthScope::test_protected_api_routes_reject_missing_auth_at_runtime -q
# 2 passed

python3 -m pytest tests/api/test_route_auth_scope.py tests/api/test_fastapi_app.py tests/api/test_production_safety.py tests/api/test_security_hardening.py tests/auth -q
# 91 passed, 1 skipped, 1 warning (Starlette/httpx deprecation from testclient)

python3 -m compileall -q services/api/fastapi_app.py tests/api/test_route_auth_scope.py
# pass
```

At Segment 4 completion time, remaining blockers were full master reconciliation and code review.

## Master reconciliation — findings closure implementation

**Updated:** 2026-06-08

Master reconciliation verified Segment 1-4 and the follow-up review-fix loop as a Builder-only findings closure. The closure now includes strictest-env production policy for token/CORS, durable AI audit-store requirements, production Redis rate-limit startup policy, scoped `/api/results`, scoped evidence-summary backtest jobs, scoped execution-lane runtime routes, explicit-local server-token web proxying, runtime `/health/backend` proxying, removal of build-time API rewrites, and same-origin local web verification docs.

Verification evidence:

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

Historical prior-closeout stop condition: full verification and post-implementation review had passed for that earlier branch. Current addendum stop condition is publication-only after clean git/remote checks; production/security readiness remains blocked.
