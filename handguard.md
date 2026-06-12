# Nautilus Builder — Handguard (2026-06-12)

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
| R-7 | Independent code review lanes required for approval wording | ⚠️ ACTIVE | Native `code-reviewer`/`architect` lanes unavailable this run | Do not label this review as approved until both lanes return evidence. |
