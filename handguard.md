# Nautilus Builder — Handguard (2026-06-13)

Active safety guardrails and invariants enforced by tests, validators, or runtime checks.

| # | Guard | Status | Enforced By | Tests |
|---|-------|--------|-------------|-------|
| 1 | Strategy spec `execution_authority=False` enforced | ✅ ACTIVE | `strategy_compiler/static_scan.py` rejects `execution_authority=True` | Static scan tests |
| 2 | No `submit_order` in generated artifacts | ✅ ACTIVE | `_FORBIDDEN_PATTERNS` in static_scan.py | Static scan tests |
| 3 | No hardcoded secrets in generated artifacts | ✅ ACTIVE | Static scan patterns for api_key/secret/eval/exec | Static scan tests |
| 4 | Production config rejects demo tokens | ✅ ACTIVE | `BuilderProductionConfig._validate_production` rejects `_DEMO_TOKENS` set | Config tests |
| 5 | Production config requires min 32 char token | ✅ ACTIVE | `_MIN_TOKEN_LENGTH` check in production config | Config tests |
| 6 | Production config rejects local artifact backend | ✅ ACTIVE | `artifact_backend must be 's3'` validation | Config tests |
| 7 | Production config rejects wildcard CORS | ✅ ACTIVE | `_is_valid_cors` rejects `*` origins | Config tests |
| 8 | Production config rejects browser API token | ✅ ACTIVE | `NEXT_PUBLIC_BUILDER_API_TOKEN` check | Config tests |
| 9 | Evidence fail-closed (factory) | ✅ ACTIVE | ValueError if in-memory evidence in production | `test_evidence_startup_guard.py` |
| 10 | Credential env keys must be venue-prefixed | ✅ ACTIVE | `_validate_env_key` in credentials.py | Credential tests |
| 11 | Credential env keys must use allowed suffixes | ✅ ACTIVE | `_ALLOWED_SUFFIXES` whitelist | Credential tests |
| 12 | Credential env keys reject forbidden names | ✅ ACTIVE | `_FORBIDDEN_KEYS` = {API_KEY, SECRET, etc.} | Credential tests |
| 13 | Credential values reject newlines/null/control chars | ✅ ACTIVE | `_validate_env_value` | Credential tests |
| 14 | Credential file chmod 0600 | ✅ ACTIVE | `env_file.chmod(stat.S_IRUSR | stat.S_IWUSR)` | Credential tests |
| 15 | Browser credential bootstrap disabled | ✅ ACTIVE | Returns error payload | Handguard tests |
| 16 | Browser secret echo disabled | ✅ ACTIVE | `browser_secret_echo: Literal[False] = False` | Handguard tests |
| 17 | LLM config rejects browser secrets | ✅ ACTIVE | `_find_forbidden_secret_key` in llm_config/service.py | LLM config tests |
| 18 | Schema name validated before SQL interpolation | ✅ ACTIVE | `safe_postgres_identifier` regex check | Postgres tests |
| 19 | Reconciliation enforced ≥60min lookback | ✅ ACTIVE | `ge=60` in config_contract.py + nautilus_runtime.py | Config contract tests |
| 20 | Risk engine bypass=False literal | ✅ ACTIVE | `Literal[False]` in RiskEngineConfig | Config contract tests |
| 21 | Strategy lane coupling disabled | ✅ ACTIVE | `strategy_lane_coupled: Literal[False] = False` | Execution lane tests |
| 22 | Credential inputs not allowed in browser | ✅ ACTIVE | `credential_inputs_allowed: Literal[False] = False` | Execution lane tests |
| 23 | Live controls require live authority | ✅ ACTIVE | `ExecutionLaneProfile` validator | Execution lane tests |
| 24 | Paper commands cannot enable live authority | ✅ ACTIVE | `ExecutionLaneCommand` validator | Execution lane tests |
| 25 | Docker image no local env files | ✅ ACTIVE | Dockerfile safety checks | `test_dockerfile_safety.py` |
| 26 | Native runner asserts not in async loop | ✅ ACTIVE | `_assert_not_in_async_loop` in sessions.py | Session tests |
| 27 | Adapter config requires concrete factories | ✅ ACTIVE | ValueError if empty data/exec client factories | Session tests |
| 28 | Promotion requires evidence refs | ✅ ACTIVE | `_assert_live_gates_present` checks evidence fields | Promotion tests |
| 29 | Binance paper adapter requires API keys | ✅ ACTIVE | ValueError if BINANCE_API_KEY/SECRET empty | Adapter config tests |
| 30 | Generic adapter fallback requires API_KEY/SECRET | ✅ ACTIVE | ValueError if keys empty in generic path | Adapter config tests |

## Watch Guards (Active but Needs Attention)

| # | Guard | Status | Concern | Recommendation |
|---|-------|--------|---------|----------------|
| W-1 | Redis rate limiter fail-open | ⚠️ ACTIVE | Falls open when Redis unavailable | Add production fail-closed mode |
| W-2 | Pipeline compilation error suppression | ⚠️ ACTIVE | `except Exception` swallows root cause | Capture exception message in step detail |
| W-3 | Double-stop on session runner | ⚠️ ACTIVE | KeyError if stop called twice | Use pop with default |
| W-4 | Evidence startup guard only at factory | ⚠️ ACTIVE | Bypassed in direct construction | Add secondary guard in service init |

## Master reconciliation — catalog-backed Nautilus replay

The `catalog_backed_replay_smoke` module validates NautilusTrader replay using synthetic historical quote ticks from the catalog_datasets layer. This is an evidence-gate smoke test, not full trading-production readiness.

| # | Guard | Status | Enforced By | Tests |
|---|-------|--------|-------------|-------|
| 31 | CATALOG_BACKED_REPLAY_SMOKE_MODE | ✅ ACTIVE | Environment gate for catalog replay smoke tests | `test_catalog_replay_ledger_updates.py` |
## 2026-06-12 Review Closure Guardrails


| ID | Guard | Status | Evidence | Required next action |
| --- | --- | --- | --- | --- |
| R-1 | Redis rate limiting must fail closed in production runtime failures | ⚠️ ACTIVE | `packages/auth/redis_rate_limit.py:71` can log `rate_limit_fallback_open` | Wire `fail_closed=True` for production construction and test Redis command failure. |
| R-2 | Pipeline compile failures must preserve redacted root cause | ⚠️ ACTIVE | `packages/pipeline/service.py:68` catches broad `Exception` | Add typed error/detail field and regression test. |
| R-3 | FastAPI startup guard must move off deprecated `on_event` | ⚠️ ACTIVE | `services/api/fastapi_app.py:203`/`:204` | Migrate to lifespan and keep fail-closed evidence test. |
| R-4 | Nautilus dependency drift must be explicit | ⚠️ WATCH | `pyproject.toml:12` pins `1.227.0`; latest checked `v1.228.0` | Run compatibility tests before upgrading or documenting intentional pin. |
| R-5 | DataTester/ExecTester evidence required before adapter production-readiness claims | ✅ ACTIVE | No DataTester/ExecTester matrix in Builder review scope | Keep all current adapter/live labels as scaffold/contract-only. |
| R-6 | AI advisory lanes must not become execution authority | ✅ ACTIVE | Credential prompt rejection and browser secret rejection remain present | Keep manual review/provenance gates before any behavior-changing use. |
| R-7 | Independent code review lanes required for approval wording | ✅ ACTIVE / SATISFIED FOR 2026-06-13 REVIEW | Native `code-reviewer` and `architect` lanes completed; verdict remains REQUEST CHANGES / BLOCK production-readiness claims | Do not label production readiness as approved until active HIGH findings are fixed. |

---

## 2026-06-13 Handguard Update — Deep Review / Legacy Closure

### Current verdict guard

Independent `code-reviewer` and `architect` lanes completed on 2026-06-13. Their combined verdict is **REQUEST CHANGES / BLOCK production-readiness claims** until active HIGH findings and adapter evidence gaps are closed. This supersedes the older note that native review lanes were unavailable; lane availability is no longer the blocker.

### Non-negotiable active guards

| ID | Guard | Status | Enforcement / evidence | Required action before promotion |
|---|---|---:|---|---|
| HG-20260613-01 | Master reconciliation — catalog-backed Nautilus replay ledger phrase must remain present in all ledgers | ✅ ACTIVE | `tests/integration/test_catalog_replay_ledger_updates.py` | Do not remove phrase without updating the contract test |
| HG-20260613-02 | `CATALOG_BACKED_REPLAY_SMOKE_MODE` must remain documented | ✅ ACTIVE | `tests/integration/test_catalog_replay_ledger_updates.py` | Keep token in this handguard until test contract changes |
| HG-20260613-03 | No production adapter claim without DataTester evidence for supported data types | ✅ ACTIVE | NT Data Testing Spec; Daedalus readiness docs | Produce per-venue artifact IDs |
| HG-20260613-04 | No production adapter claim without ExecTester evidence for supported execution capabilities | ✅ ACTIVE | NT Execution Testing Spec; Daedalus readiness docs | Produce per-venue artifact IDs |
| HG-20260613-05 | Reconciliation is required for live execution readiness | ✅ ACTIVE | NT Execution Testing Spec; `execution_lane_validation.py` | Provide reconciliation readiness record |
| HG-20260613-06 | Missing health data must fail closed, not default healthy | ⚠️ ACTIVE RISK | `graph_runner.py` defaults for `api_connected` / `data_quality_ok` | Change defaults and add regression tests |
| HG-20260613-07 | Redis production rate limiting must fail closed when Redis is unavailable | ⚠️ ACTIVE RISK | `packages/auth/redis_rate_limit.py` | Force production `fail_closed=True` and test it |
| HG-20260613-08 | Pipeline compile failures must preserve redacted root cause | ⚠️ ACTIVE RISK | `packages/pipeline/service.py` | Record exception type/message and test it |
| HG-20260613-09 | Adapter submit/modify/cancel exceptions must not be swallowed | ⚠️ ACTIVE RISK | Daedalus adapter execution modules | Emit typed errors / rejection events / logs |
| HG-20260613-10 | `run_full_stack` is local manifest/dry-run only | ✅ ACTIVE | `run_full_stack.py`; runtime runbook | Do not promote it as a production supervisor |
| HG-20260613-11 | AI/EvoMap/LangChain/LangGraph lanes are advisory/process-only | ✅ ACTIVE | AI lane topic authority guard | No TradeAction, order routing, active config mutation, or core stream ACKs from AI |
| HG-20260613-12 | Telegram/aiogram-dialog menus stay downstream-only | ✅ ACTIVE | Telegram gateway runbook and formatter | Menus may display/request operator actions, never generate signals or submit orders |
| HG-20260613-13 | Compatibility shims require explicit owner/expiry | ⚠️ WATCH | `menu_service`, `as_legacy_dict`, topic aliases | Add owner/expiry and closure tests |
| HG-20260613-14 | Builder/Daedalus NT version drift must be tracked | ⚠️ WATCH | Builder `1.227.0` vs Daedalus `1.228.0` | Align pins or document migration deadline |

### Promotion checklist added by this review

Before any future “ready” or “merge-ready” wording, require all of:

1. `uv run pytest tests/integration/test_catalog_replay_ledger_updates.py -q` passes in Builder.
2. Active HIGH findings in `findings.md` are either fixed with tests or explicitly accepted with owner/deadline.
3. Each claimed adapter has DataTester and ExecTester artifact IDs for the subset of supported capabilities.
4. Each live execution profile has reconciliation readiness, kill-switch/risk/credential evidence, and operator approval IDs.
5. AI/Telegram projection schemas are versioned and remain one-way downstream.
6. Active semantic legacy/deprecation shims have owner, expiry, and removal tests.

Master reconciliation — catalog-backed Nautilus replay

`CATALOG_BACKED_REPLAY_SMOKE_MODE` remains the current catalog-backed replay smoke guard token.

---

## 2026-06-17 Handguard Update — TradeHUD Seam Guards + Regression Gates

### Current verdict guard (2026-06-17)

Single-lane review (native dual-lane `code-reviewer`/`architect` subagents unavailable in this Codex environment). Verdict: **REQUEST CHANGES** — two new HIGH regressions (stale OpenAPI snapshot, removed root page) break CI. Do not treat `master` as green until H-20260617-01 and H-20260617-02 are fixed.

### New TradeHUD-seam guards

| ID | Guard | Status | Enforced By | Tests |
|----|-------|--------|-------------|-------|
| 32 | TradeHUD is read-only / no order authority | ACTIVE | `packages/tradehud_contracts/` has no submit surfaces; SSE route declares read-only | `tests/tradehud_contracts/test_nd_safety_contracts.py` |
| 33 | `missing != true_zero` normalizer contract | ACTIVE | `normalizer.py` preserves None vs explicit 0 | `test_nd_normalizer_contracts.py` (174 contract tests) |
| 34 | Redis URL never exposed in health/snapshot | ACTIVE | `config.sanitize_redis_url()`; SSE route `_SENSITIVE_SUFFIXES`/`_SENSITIVE_WORDS` redaction | `tests/tradehud_redis/test_health_sanitization.py` |
| 35 | TS types mirror Python models | ACTIVE | `apps/web/lib/tradehud/types.ts` ↔ `packages/tradehud_contracts/models.py` | reducer/selectors tests |
| 36 | TradeHUD seed/replay scripts local-dev only | ACTIVE (intent) | header docstrings | needs runtime localhost guard (M-20260617-05) |

### New regression guards (must be restored)

| ID | Guard | Status | Concern | Required action |
|----|-------|--------|---------|-----------------|
| HG-20260617-01 | OpenAPI snapshot must match live schema | BROKEN | `test_openapi_snapshot.py` fails — 4 tradehud paths added but not snapshotted | Regenerate `tests/api/openapi_snapshot.json` and commit |
| HG-20260617-02 | Root `app/page.tsx` must satisfy web contract tests | BROKEN | 11 `tests/web/*` tests fail — root page removed by standalone merge | Restore root page OR update tests to assert `(builder)/page.tsx` |
| HG-20260617-03 | CI must be green before merge-ready claims | BLOCKED | 12 failures across snapshot + web contracts | Fix HG-20260617-01 and -02 first |

### Updated non-negotiable active guards (carry-forward + new)

| ID | Guard | Status | Enforcement / evidence | Required action |
|----|-------|--------|------------------------|-----------------|
| HG-20260613-01..14 | (all prior guards) | unchanged | see 2026-06-13 table above | carry forward |
| HG-20260617-04 | TradeHUD SSE route must sit behind auth middleware | WATCH | `services/api/routes/tradehud_sse.py` has no explicit `Depends(auth)` | Confirm middleware coverage or add dependency (M-20260617-03) |
| HG-20260617-05 | `redis_adapter.py` LOC ceiling | WATCH | 843 LOC single module | Plan split once stable (M-20260617-01) |
| HG-20260617-06 | Legacy stream map needs owner/expiry | WATCH | `config.py:14` `_LEGACY_STREAM_MAP` | Add owner/expiry header + opt-in test (M-20260617-02) |

### Updated promotion checklist (2026-06-17)

Before any future "ready" / "merge-ready" wording, require all of the 2026-06-13 checklist plus:

7. `pytest tests/api/test_openapi_snapshot.py tests/web/ -q` is green in Builder.
8. TradeHUD SSE route is confirmed behind auth middleware (or explicitly documented as gateway-auth-only).
9. `tradehud_seed_redis.py` refuses non-local Redis (or carries an explicit override flag).
10. Dead deprecated TS files (`apiClient.ts`, `OperatorAppShell.tsx`) are deleted or have a documented removal owner.

Master reconciliation — catalog-backed Nautilus replay

`CATALOG_BACKED_REPLAY_SMOKE_MODE` remains the current catalog-backed replay smoke guard token.


---

## 2026-06-21 backlog closure — guard status update

The 2026-06-21 closure pass closed all P0 and P1 items with regression tests.
Suite: 1850 passed, 1 skipped, 0 failed. Guards above remain ACTIVE; the closure
added/verified:

- TradeHUD `/api/tradehud/*` routes are now route-level auth + rate-limit gated
  (SSE stream never starts before auth). Read-only/advisory posture intact.
- Redis rate limiter defaults fail-closed (bare construction denies when Redis is
  down). Production fail-closed behavior proven by default.
- Evidence storage factory guard added (defense in depth for direct construction).
- Pipeline compile failures preserve a redacted root cause; secrets scrubbed.
- Native TradingNode stop is idempotent with NOT_FOUND / STOP_TIMEOUT guarantees.
- LLM transport uses explicit TLS verification + timeout.
- Legacy `nautilus:tradehud:*` stream map has owner / expiry / removal-criteria;
  default namespace is `nd`, legacy requires explicit opt-in.
- Authority scan remains green; AI/TradeHUD cannot submit orders or collect creds.

Verdict may move from REQUEST CHANGES once adapter DataTester/ExecTester/
reconciliation evidence per claimed venue is added (unchanged open work).

---
## 2026-06-21 remaining findings closure (ultragoal pass) — guard status update

This ultragoal pass (TDD) closes the remaining 2026-06-21 review findings. Guards
remain ACTIVE; production-readiness wording is still BLOCKED until adapter
evidence lands.

### Guards advanced/closed this pass
- **Guard #9 (tradehud seed/replay refuses non-local Redis)**: ✅ ADVANCED.
  `scripts/tradehud_replay_nd_fixtures.py` now enforces LOCAL DEV ONLY at runtime:
  host allowlist (localhost/127.0.0.1/::1), environment guard
  (BUILDER_ENV/APP_ENV/ENVIRONMENT = production/prod/staging/stage -> SystemExit),
  a scary `--allow-nonlocal-redis-for-fixture-replay` override that bypasses the
  HOST check ONLY (never the production-env guard), and `redact_redis_url()` in
  all logs. Covered by 22 test cases.
- **R-4 / HG-20260613-14 (Nautilus dependency drift)**: ✅ CLOSED. Pin upgraded
  1.227.0 -> 1.228.0, aligned with Nautilus-Daedalus and the official release.
  `engine_contract.py` + `pyproject.toml` + `uv.lock` updated; drift-guard tests
  pass against the new pin.
- **TradeHUD SSE production Redis-unavailable**: ✅ CLOSED. After `stream_error`
  in production (configured-but-unavailable Redis), the generator stops instead
  of presenting a synthetic (alive-looking) snapshot. Local/dev fallback
  unchanged.
- **Adapter/readiness overstatement**: wording already conservative; hardened
  with defensive tests so READY cannot be claimed without evidence types and
  no live/production-named capability can be READY.

### Still OPEN (unchanged gate)
- Verdict remains REQUEST CHANGES / NOT PRODUCTION-READY / NOT MERGE-READY.
- Full production/merge-ready gating still requires DataTester/ExecTester/
  reconciliation artifacts per claimed venue/capability. Builder remains
  scaffold/contract/evidence-gated only.
- Deferred (locked by green tests): execution_lane module split (P2-2),
  tradehud redis_adapter module split (P2-3).

---
## 2026-06-21 post-fix rescan — additional improvement

Read-only rescan after the ultragoal closure pass. Suite green at time of
rescan (1873 passed, 1 skipped, 0 failed).

### Closed this rescan
- **SSE staging parity (P2-4 consistency):** `services/api/routes/tradehud_sse.py`
  `_is_production_env()` previously matched only `== "production"`, so in
  `BUILDER_ENV=staging` a configured-but-unavailable Redis feed silently fell
  back to a synthetic snapshot (the exact broken-live-feed-looking-alive failure
  P2-4 was meant to prevent). Extended to treat `staging` and `production` as the
  strict/non-local set, matching the canonical `BuilderEnvironment` (LOCAL /
  STAGING / PRODUCTION). New staging test asserts stream_error + stop; local/dev
  fallback unchanged.

### Tracked follow-ups (architecture, behind a green test gate)
- **R2** `services/api/fastapi_app.py` is ~1090 LOC (app factory + route
  registration + startup + evidence guard in one module). Split candidate.
- **R3** `packages/tradehud_contracts/redis_adapter.py` is ~843 LOC (read/write/
  redaction/normalization/health mixed). This is the deferred P2-3 split;
  behavior is locked by green tests, split is a follow-up.
- Optional: add a `ruff` lint gate to CI (tool installed; currently CI runs only
  `compileall` + pytest + TS typecheck for Python).

### Still NOT production-ready
Adapter/live claims still require DataTester/ExecTester/reconciliation artifacts
per claimed venue/capability. Builder remains scaffold/contract/evidence-gated
only.

---
## 2026-06-21 $omo refactor pass — R2/R3/ruff closed

Module-split and lint-gate refactor ($omo:refactor + $omo:programming), behind the
green test gate (zero regression). Full suite 1881 passed, 1 skipped, 0 failed.

### Closed this pass
- **R3 — redis_adapter split (P2-3):** split the 843-LOC monolith into
  `redis_normalizers.py` (parsers + `parse_stream_entry`), `redis_snapshot_builder.py`
  (`build_snapshot_from_redis`), and a thin `redis_adapter.py` (264 LOC,
  connection/IO only) with backward-compatible re-exports. Locked by 7 new
  module-split invariants (public/internal symbol reachability, size <=400 LOC,
  no parser re-definition in the adapter). tradehud tests 279 passed.
- **R2 — fastapi_app helper extraction:** extracted the pure env/config startup
  helpers (`_strictest_configured_env`, `_cors_origins_from_env`,
  `_validate_startup_policy`, `_register_env_dev_token`, `_env_user_project_context`,
  `_default_ai_audit_store`, `_UNSAFE_DEV_TOKENS`) into `services/api/_app_env.py`;
  fastapi_app re-exports them (backward compat). fastapi_app 1090 -> 1014 LOC. The
  create_fastapi_app route closures (shared closure state) were deliberately left in
  place. tests/api 191 passed.
- **Ruff lint gate:** added `[tool.ruff]` (select E4/E7/E9/F) + a `Lint (ruff)` step
  in `.github/workflows/ci.yml` (backend job). Fixed all 22 pre-existing findings in
  packages/services, including 3 real F821 "Undefined name FastAPI" latent bugs in
  `app_factory.py`/`middleware.py`. `ruff check packages services` is clean.

### Still NOT production-ready
Adapter/live claims still require DataTester/ExecTester/reconciliation artifacts per
claimed venue/capability. Builder remains scaffold/contract/evidence-gated only.

---
## 2026-06-21 frontend/backend reconciliation ($omo:frontend)

Reconciliation of the frontend API layer against the backend route surface (50
backend routes). Full Python suite 1881 passed, 1 skipped, 0 failed; web contract
tests 75 passed; lib/api.test.ts 12 passed; tsc clean.

### Cleanup — dead artifacts removed
- `apps/web/lib/apiClient.ts` (DELETED): explicitly-`@deprecated` backward-compat
  shim superseded by `api.ts`; zero imports, zero test references.
- `apps/web/components/shell/OperatorAppShell.tsx` (DELETED): superseded by
  BuilderShell; zero component imports, zero test references (contract test
  requires BuilderShell, not OperatorAppShell). Stale CSS comment updated.

### Reconnected missing read-only API
Added `api.ts` helpers + `types.ts` for safe observational backend routes that
previously had no frontend connection (all READ-ONLY, verified live):
- `fetchReadinessMatrix` -> GET /api/readiness (readiness matrix; live_execution
  remains out_of_scope).
- `fetchEvidenceForLineage` -> GET /api/evidence.
- `fetchRuntimeEventsReplay` -> GET /api/runtime-events/replay.
- `fetchWorkflowLineageStatus` -> GET /api/workflow/lineages/{id}/status.
- `fetchWorkflowResultSuggestions` -> GET /api/workflow/results/{id}/suggestions.

### Safety contract enforced (NOT reconnected)
Execution-authority endpoints are deliberately NOT wired to the frontend, per the
hard read-only/advisory contract enforced by `tests/web/test_execution_lane_ui_contract.py`:
- No execution-lane SESSION modeling or lifecycle (start/stop) in the UI. An
  attempted `ExecutionLaneSessionStatus` read-only helper was REVERTED after the
  contract test caught it forbidding `ExecutionLaneSession` in the frontend.
- No `submit_order`, no credential inputs, no session start/stop, no
  `/api/execution-lane/sessions/start`, no worker run-once, no pipeline-mutating
  endpoints.

### Resolved (frontend vitest page tests)
The 7 frontend vitest page tests that previously failed now pass (206 passed |
4 skipped | 0 failed). Root cause was NOT a `next/navigation`/`useRouter` mock
gap; each page test's `vi.mock("...")` module specifier had one extra `../`
relative to the import path the page-under-test uses, so the mock factory never
matched and the real component/`lib/api` rendered (surfacing as `useRouter` /
`invariant expected app router` / `parse URL` errors). Fix: corrected the
`vi.mock` specifier in 7 test files to exactly match the page import path. Pure
test-infrastructure change: no production code, no api.ts/types.ts symbols, no
test assertions weakened, no execution authority wired (execution-lane UI
contract still green). `tsc --noEmit` clean.

### Still NOT production-ready
Adapter/live claims still require DataTester/ExecTester/reconciliation artifacts
per claimed venue/capability.


## 2026-06-22 Adoption Validation Report — guard status ($omo + TDD)

### Guards verified ACTIVE after adoption

- **AI advisory-only boundary**: HELD. `InstructorDraftProvider` is
  extraction-only (PR3). No tools, no agent invocation, no order authority.
  Forbidden credential/order prompts rejected before provider call
  (15 contract tests). Authority scan PASSED.
- **No submit_order/TradeAction in production code**: HELD. Authority scan
  PASSED across all adoption (instructor, httpx, protocols, alembic).
- **TLS verification**: HELD. `HttpxJsonTransport.verify == True` by default
  (PR4). `test_transport_tls_verification_enabled_by_default` asserts this.
- **No secrets in metadata/logs**: HELD. `InstructorDraftProvider.last_metadata()`
  allow-list scrubbed (PR3). HttpxJsonTransport redacts raw response from
  error messages (PR4).
- **No SQLAlchemy ORM swap**: HELD. Alembic (PR5) is migrations only.
  Raw SQL/psycopg repositories unchanged.
- **Custom migration runner intact**: HELD. Alembic baseline is stamp-only
  Phase 1; `packages/postgres/migrations.py` unchanged.
- **CATALOG_BACKED_REPLAY_SMOKE_MODE**: ACTIVE (token preserved in this ledger).

### Type safety guard (new, PR1)

- basedpyright standard mode on 7 packages, 0 errors. CI `static-analysis`
  job enforces type-checking + pip-audit on every push/PR.
- Two rules (`reportOptionalMemberAccess`, `reportArgumentType`) set to
  `"none"` for the `require_context()` tuple-correlation pattern — documented
  in pyproject.toml; tracked for future optional-narrowing hardening pass.

### Still NOT production-ready

Adoption of basedpyright/instructor/httpx/alembic does NOT make any adapter or
venue production-ready. Adapter/live claims still require DataTester,
ExecTester, reconciliation, kill-switch/risk/credential, and operator-approval
evidence per venue/capability. The AI lane remains advisory-only and cannot
submit orders.

`CATALOG_BACKED_REPLAY_SMOKE_MODE` remains the current catalog-backed replay
smoke guard token.

## HG-20260622-23 — Prompt routing must use installed NT skills

- **Status**: ACTIVE.
- **Rule**: Prompt packs and agent handoffs must name the installed
  `superpowers:nt` router and installed NT subskills. Do not route work to
  nonexistent skill names such as `nt-ai-strategy-builder` unless that skill is
  actually created, installed, tested, and listed in the session skill catalog.
- **Required route for AI/web strategy-builder work**: `superpowers:nt` →
  `nt-architect` → `nt-implement`/`nt-strategy-builder`/`nt-signals` as needed
  → `nt-backtest` → `nt-testing` → `nt-review`. Add `nt-adapters` or `nt-live`
  only when adapter/runtime lifecycle work is actually in scope.
- **Safety boundary**: Prompt-generated output is advisory draft material. It
  cannot bypass StrategySpec validation, NautilusTrader backtest evidence,
  promotion gates, manual approval, credential handling rules, or runtime
  authority separation.
- **Verification evidence**: `doc/nautilus_builder_implementation_prompts.md`
  was corrected on 2026-06-22 and this guardrail was added to prevent drift.

## 2026-06-22 review-fix guardrail additions

| ID | Guard | Status | Enforced By | Tests |
|---|-------|--------|-------------|-------|
| HG-20260622-01 | TradeHUD browser SSE/snapshot calls stay same-origin; browser must not bypass server auth proxy with a public API base | ACTIVE | `apps/web/lib/tradehud/replay-feed.ts` returns same-origin API base for TradeHUD feed clients | `apps/web/lib/tradehud/sse-feed.test.ts` |
| HG-20260622-02 | TradeHUD SSE connection failure must fail closed/degraded, not silently fall back to mock market data | ACTIVE | SSE error path dispatches `redis_disconnected` and no mock `SNAPSHOT` fallback | `apps/web/lib/tradehud/sse-feed.test.ts` |
| HG-20260622-03 | AI draft apply/save must preserve the generated StrategySpec; save failure must be visible | ACTIVE | `apply_draft_to_strategy(..., spec=...)` and `AiStrategyCopilot` pass/save the same `result.spec` | `test_persistent_audit_store.py`, `AiStrategyCopilot.test.tsx` |
| HG-20260622-04 | Status-only evidence is not proof of readiness | ACTIVE | Evidence summary emits `status_only`; lifecycle/evidence refs derive unknown instead of passed | `test_evidence_summary.py`, lifecycle Vitest tests |
| HG-20260622-05 | Shadow promotion requires complete backend evidence refs | ACTIVE | `PipelineRunPanel` requires `validation_report`, `backtest_result`, `gate_compatibility_report` before request | `PipelineRunPanel.test.tsx` |
| HG-20260622-06 | Result dashboard must not synthesize placeholder provenance IDs | ACTIVE | `workflow_results.py` omits placeholder strategy-version artifact; UI renders unavailable values explicitly | `test_workflow_results.py`, `ResultsDashboard.test.tsx` |
| HG-20260622-07 | SSE keepalive/open status must not be labeled as synthetic data | ACTIVE | `TradeHudTopBar.tsx` renders `SSE CONNECTED` for `feedStatus=live` | `TradeHudTopBar.test.tsx` |
