# Nautilus Builder Deep Review Findings

**Review date:** 2026-05-28 (updated deep review)
**Target repository:** `/home/mok/projects/nautilus_builder`
**Reference repository:** `/home/mok/projects/Nautilus-Daedalus` (read-only alignment reference)
**Review mode:** `$superpowers:code-review` + `$superpowers:nt-review` (primary), with `nt-architect`, `nt-adapters`, `nt-live`, `nt-testing`.

## Verdict

**Recommendation: COMMENT** — no CRITICAL or BLOCK issues remain. Several HIGH/MEDIUM items warrant attention before claiming Builder MVP or NautilusTrader production readiness.

## Architectural Status: WATCH

The execution lane TradingNode contract is well-designed but introduces a direct `nautilus_trader` runtime dependency. When NautilusTrader upgrades from v1.223 to v1.224+, the `BacktestVenueConfig.trade_execution` default change and adapter API shifts will need explicit migration testing. The pinned version protects against accidental breakage but creates technical debt.

## Verification evidence

```bash
cd /home/mok/projects/nautilus_builder

python3 -m compileall -q packages services tests
# Clean

python3 -m pytest tests/ -q --tb=line
# 401 passed, 5 warnings
```

## Positive findings (preserved from prior review)

- Builder-vs-Daedalus-vs-NautilusTrader boundaries are explicit in `doc/nautilus_builder_hardguards.md`, `doc/nautilus_builder_spec.md`, and `README.md`.
- Compile artifacts set `execution_authority=False` for both backtest and signal-preview profiles.
- Promotion payloads set `may_submit_order=False`, `may_create_trade_action=False`.
- Backtest config rejects explicit live credentials: `if credentials: raise ValueError`.
- `execution_lane/credentials.py` uses strict venue-prefixed key validation, owner-only file permissions, and never echoes secrets.
- `NautilusTradingNodeRuntimePlan` uses `Literal[False]` type guards for browser_credentials, credential_inputs, strategy_lane_coupling.
- AI builder routes through `validate_strategy_spec()` and `StrategySpec.model_validate()` (fixed since prior review).
- Forbidden-token coverage in `strategy_validation/policy.py` now includes all hardguarded terms: `api_key`, `secret_key`, `credential`, `broker_order`, `exchange_order`, `TradeAction`.
- 401 tests pass across 20+ test directories.
- No hardcoded secrets in production code.
- No blocking calls (`time.sleep`, `requests.get`, etc.) in hot paths.
- No `submit_order` or `TradeAction` references in builder-side packages (enforced by test suite).
- `_walk_strings` in `validators.py` recursively checks keys and values for forbidden tokens — correct.
- `ExecutionLaneProfile` enforces `reconciliation_lookback_mins >= 60` at model level via `Field(ge=60)`.
- `_SECRET_KEYS` in `execution_lane/models.py` rejects credentials in profiles, commands, and reports recursively.
- `BacktestRunManifest` uses `Literal[False]` for `credentials_used`, `live_trading_enabled`, `execution_authority`.
- OpenAI-compatible provider uses `urllib.request` (no third-party HTTP dependency) with configurable timeout.
- Artifact store uses scoped `artifact://builder/` URIs with checksum validation.
- `OpenAICompatibleProviderConfig` validates all required fields in `__post_init__`.

## Findings by severity

### CRITICAL (0)

None.

### HIGH (3)

#### HIGH-1 — NautilusTrader pinned at v1.223.0, upstream at v1.226+

**Evidence**

- `pyproject.toml:7` pins `nautilus_trader==1.223.0`.
- `packages/backtest_runner/engine_contract.py:3` hardcodes `NAUTILUS_TRADER_VERSION = "1.223.0"`.
- v1.224+ renamed `fill_limit_at_touch` → `fill_limit_inside_spread`, removed Coinbase IntX adapter, changed `InstrumentProvider` default methods.
- v1.223.0 changed `trade_execution` default to `True` in `BacktestVenueConfig`.
- `packages/backtest_runner/config_builder.py` does not explicitly set `trade_execution` in the venue config, relying on defaults.
- Daedalus reference also pinned at `nautilus_trader==1.223.0`.

**Risk**

When Builder upgrades to v1.224+, any BacktestVenueConfig that assumed the old `trade_execution=False` default will silently switch to trade execution. If the runtime plan expects observation-only backtests, this becomes a correctness issue.

**Fix**

- Explicitly set `trade_execution=True` (or `False` with documented intent) in `config_builder.py`.
- Add a NautilusTrader version alignment test that fails on major/minor version drift.
- Plan a v1.224+ upgrade with explicit migration checklist covering all NT version changes.

#### HIGH-2 — `TestJobRecord` / `TestResultRecord` Pydantic models collide with pytest class collection

**Evidence**

- `packages/workflow_spine/models.py:63` defines `class TestJobRecord(BaseModel)`.
- `packages/workflow_spine/models.py:82` defines `class TestResultRecord(BaseModel)`.
- Pytest raises `PytestCollectionWarning` (5 warnings total across 4 test files) because classes starting with `Test` have `__init__` constructors.

**Risk**

While currently warnings-only, this can mask real test collection failures or cause confusing test discovery behavior. Future pytest versions may escalate this to an error.

**Fix**

- Rename to `WorkflowJobRecord` / `WorkflowResultRecord` (they are not test classes).
- Update all import sites across the codebase.
- Add a linter rule that flags Pydantic model classes starting with `Test`.

#### HIGH-3 — Legacy fixture ref bypass in promotions service

**Evidence**

- `packages/promotions/service.py:19` accepts `allow_legacy_fixture_refs=True` (default).
- `services/api/routes/promotions.py:23` passes `allow_legacy_fixture_refs=not strict_evidence`.
- When `strict_evidence` is not requested (default), legacy unscoped fixture refs pass through promotion validation.
- The `_validate_evidence` method skips artifact store resolution when `not requires_artifacts`, meaning legacy refs bypass the checksum and binding validation.

**Risk**

Non-strict promotion requests can reference artifacts that lack proper scope lineage. This weakens the evidence chain for promotion decisions.

**Fix**

- Flip default to `allow_legacy_fixture_refs=False`.
- Add deprecation warning when legacy refs are used.
- Require `strict_evidence=True` for all non-dev promotion paths.

### MEDIUM (7)

#### MEDIUM-1 — Execution lane sessions only support Binance adapter

**Evidence**

- `packages/execution_lane/sessions.py:383-414` hardcodes `_binance_client_configs()` with Binance-specific imports and config construction.
- Non-Binance venues fall through to generic `LiveDataClientConfig()` / `LiveExecClientConfig()` without credential wiring (line 387-389).
- `packages/adapter_registry/` exists but is not wired to the session builder.

**Risk**

Adding a new adapter (e.g., Bybit, OKX, or a Daedalus custom adapter) requires modifying `sessions.py` directly. The adapter registry package is disconnected from execution lane resolution.

**Fix**

- Route adapter resolution through `packages/adapter_registry/` with a plugin-style adapter config builder interface.
- Each registered adapter provides its own client config builder function.
- Remove the hardcoded Binance branch.

#### MEDIUM-2 — `NativeTradingNodeSessionRunner` blocks caller thread

**Evidence**

- `packages/execution_lane/sessions.py:107-146` `NativeTradingNodeSessionRunner.start()` calls `node.run()` and `node.stop()` synchronously.
- The class itself is guarded behind `BUILDER_EXECUTION_LANE_TRADINGNODE_RUNNER=native` env var.
- But if used from a FastAPI handler, it would block the event loop.

**Risk**

In the default API server context, if an operator enables the native runner, the entire API server hangs until the TradingNode finishes. This is documented as operator-opt-in but has no runtime guard.

**Fix**

- Add explicit guard: if runner is `native` and caller is the API event loop, reject with a clear error.
- Document that native runner must be used from a worker process, not the API server.

#### MEDIUM-3 — `ExecutionLaneService` uses in-memory storage with no persistence

**Evidence**

- `packages/execution_lane/service.py` stores profiles, commands, sessions in `dict` attributes.
- No disk or database backing. Service restart loses all state.
- The `workflow_spine/` package has Postgres repository infrastructure but execution lane doesn't use it.

**Risk**

In production, a service restart drops all execution lane state (profiles, running sessions, queued commands). This limits the execution lane to single-process dev/demo use.

**Fix**

- Wire execution lane persistence to the existing Postgres repository infrastructure.
- At minimum, serialize critical state to disk for recovery.

#### MEDIUM-4 — `NautilusTradingNodeRuntimePlan.config_contract` is untyped `dict[str, Any]`

**Evidence**

- `packages/execution_lane/nautilus_runtime.py:43` defines `config_contract: dict[str, Any]`.
- The `_config_contract()` helper constructs a well-structured dict but it's not schema-validated.
- API routes serialize this directly to JSON.

**Risk**

No compile-time or validation-time guarantee that the config contract structure matches what TradingNode actually expects. Changes to the contract shape won't be caught by tests.

**Fix**

- Define a Pydantic model for the config contract.
- Validate at construction time.
- Add contract tests.

#### MEDIUM-5 — No rate limiting on AI builder draft endpoint

**Evidence**

- `services/api/app.py` registers `POST /api/ai-builder/draft` with no rate limiting middleware.
- `OpenAICompatibleDraftProvider` makes outbound HTTP calls to operator-configured LLM endpoints.
- No authentication or rate limiting on the draft generation route.

**Risk**

Unauthenticated users could flood the draft endpoint, causing excessive LLM API costs or denial of service.

**Fix**

- Add rate limiting middleware to AI builder routes.
- Require authentication for draft generation.
- Add cost tracking/logging for LLM API calls.

#### MEDIUM-6 — `reconciliation_lookback_mins` clamping discrepancy resolved

**Evidence (updated)**

- `ExecutionLaneProfile.reconciliation_lookback_mins` now uses `Field(default=60, ge=60)` — enforced at model level.
- The runtime plan's `open_check_lookback_mins` and `position_check_lookback_mins` are clamped via `max(60, profile.reconciliation_lookback_mins)`.
- The discrepancy from prior review is now resolved.

**Status: RESOLVED**

#### MEDIUM-7 — Frontend E2E tests depend on Playwright browser installation

**Evidence**

- `apps/web/e2e/builder-shell.spec.ts` requires Chromium installed via `npx playwright install chromium`.
- Current environment doesn't have browsers installed, so E2E tests were skipped.
- Python-side web contract tests (49 tests in `tests/web/`) compensate but don't test real browser rendering.

**Risk**

CSS/rendering regressions and AntD v6 style issues won't be caught until browsers are installed and E2E is run.

**Fix**

- Add Playwright browser installation to the CI/deployment pipeline.
- Document the E2E prerequisite in README.

### LOW (5)

#### LOW-1 — `compile_hash` uses legacy SHA-256 derivation in backtest jobs route

**Evidence**

- `services/api/routes/backtest_jobs.py:268-269` computes a "legacy_hash" from `compile_artifact_id`.
- This appears to be backward-compat for older job records.

**Fix**

- Document the legacy hash and plan its removal once all stored jobs use the canonical hash format.

#### LOW-2 — `workflow_spine/storage_config.py` accepts legacy schema alias

**Evidence**

- `tests/workflow_spine/test_storage_config.py:14` tests that a legacy schema alias is accepted without a `shadow_field`.

**Fix**

- Document the alias and add a deprecation timeline.

#### LOW-3 — `runtime_label` in `NautilusTradingNodeRuntimePlan` is verbose

**Evidence**

- `packages/execution_lane/nautilus_runtime.py:31` uses `Literal["python_live_integration_specific"]`.

**Fix**

- Consider shortening to `"python_integration"` or documenting why the full label is needed. Low priority.

#### LOW-4 — No typed error hierarchy for builder service errors

**Evidence**

- Service methods raise `ValueError` for validation failures, `RuntimeError` for internal errors.
- No custom error hierarchy (`BuilderValidationError`, `CredentialSlotError`, etc.).

**Fix**

- Introduce a small typed error hierarchy for cleaner API error mapping and test assertions.

#### LOW-5 — `DESIGN.md` is present but not referenced from `README.md`

**Evidence**

- `DESIGN.md` exists as the UI source of truth but `README.md` doesn't link to it.

**Fix**

- Add a reference in README under the Architecture or UI section.

## Architecture Watchlist

### WATCH-1 — NautilusTrader version pin creates upgrade friction

- The pinned `nautilus_trader==1.223.0` is 3+ minor versions behind the latest.
- Builder should plan an explicit upgrade with a migration checklist that covers: `BacktestVenueConfig.trade_execution`, adapter config API changes, `InstrumentProvider` method changes.
- The reference Daedalus repo is also pinned at v1.223.0, so both repos should upgrade in lockstep.

### WATCH-2 — Execution lane couples Builder to Binance adapter

- The current session builder only fully supports Binance. Non-Binance venues get generic configs without credential wiring.
- The adapter registry package exists but isn't wired to the execution lane session builder.
- As the adapter registry grows, this will need generalization.

### WATCH-3 — DataTester/ExecTester evidence is architecturally external

- Builder correctly gates on evidence refs but doesn't produce them.
- This is by design (Builder is authoring, not testing), but the boundary should be explicit in docs.

### WATCH-4 — OpenAI-compatible provider uses `urllib.request.urlopen` without certificate pinning

- `packages/ai_builder/provider.py:246` uses `urllib.request.urlopen` for LLM endpoint calls.
- No custom SSL context or certificate pinning.
- The `# noqa: S310` suppression acknowledges this.
- For operator-configured endpoints, this is acceptable but should be documented.

## Legacy / Deprecation Inventory

| Item | Location | Status | Action | Priority |
|---|---|---|---|---|
| Legacy compile hash | `services/api/routes/backtest_jobs.py:268` | Active backward-compat | Document + deprecation timeline | LOW |
| Legacy fixture refs | `packages/promotions/service.py:19` | Active with `allow_legacy_fixture_refs=True` default | **Flip default to `False`** | HIGH |
| Legacy storage schema alias | `packages/workflow_spine/storage_config.py` | Accepted without `shadow_field` | Document + deprecation timeline | LOW |
| `TestJobRecord` naming | `packages/workflow_spine/models.py:63` | Causes pytest warnings | **Rename to `WorkflowJobRecord`** | HIGH |
| `TestResultRecord` naming | `packages/workflow_spine/models.py:82` | Causes pytest warnings | **Rename to `WorkflowResultRecord`** | HIGH |
| NautilusTrader v1.223.0 pin | `pyproject.toml:7`, `engine_contract.py:3` | 3+ versions behind | Plan upgrade | HIGH |
| `PAPER_STRATEGY_PATH` string | `sessions.py:15` | Hardcoded module path | Extract to config | LOW |
| `_DEFAULT_ENV_FILE` constant | `credentials.py:24` | Hardcoded `.env.execution.local` | Acceptable for current scope | INFO |

## Synthesis

- **code-reviewer recommendation:** COMMENT
- **architect status:** WATCH
- **final recommendation:** COMMENT

Address HIGH-1 (NautilusTrader version alignment), HIGH-2 (model naming), and HIGH-3 (legacy fixture bypass) before treating the codebase as merge-ready for a significant release.

## Master reconciliation — catalog-backed Nautilus replay

The `catalog_backed_replay_smoke` smoke test validates BacktestNode catalog replay using synthetic historical quote ticks. This is a wiring and data-flow check — not full trading-production readiness.
