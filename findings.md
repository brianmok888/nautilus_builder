# Nautilus Builder Deep Review Findings

**Review date:** 2026-05-28
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
- Backtest config rejects explicit live credentials.
- `execution_lane/credentials.py` uses strict venue-prefixed key validation, owner-only file permissions, and never echoes secrets.
- `NautilusTradingNodeRuntimePlan` uses `Literal[False]` type guards for browser_credentials, credential_inputs, strategy_lane_coupling.
- AI builder now routes through `validate_strategy_spec()` and `StrategySpec.model_validate()` (fixed since prior review).
- Forbidden-token coverage in `strategy_validation/policy.py` now includes all hardguarded terms: `api_key`, `secret_key`, `credential`, `broker_order`, `exchange_order`, `TradeAction`.
- 401 tests pass across 20+ test directories.
- No hardcoded secrets in production code.
- No blocking calls (`time.sleep`, `requests.get`, etc.) in hot paths.
- No `submit_order` or `TradeAction` references in builder-side packages (enforced by test suite).

## Findings by severity

### CRITICAL (0)

None.

### HIGH (3)

#### HIGH-1 — NautilusTrader pinned at v1.223.0, upstream is at v1.226+

**Evidence**

- `pyproject.toml:7` pins `nautilus_trader==1.223.0`.
- v1.224+ renamed `fill_limit_at_touch` → `fill_limit_inside_spread`, removed Coinbase IntX adapter, changed `InstrumentProvider` default methods.
- v1.223.0 changed `trade_execution` default to `True` in `BacktestVenueConfig`.
- `packages/backtest_runner/config_builder.py` does not explicitly set `trade_execution` in the venue config, relying on defaults.

**Risk**

When Builder upgrades to v1.224+, any BacktestVenueConfig that assumed the old `trade_execution=False` default will silently switch to bar-only execution. If the runtime plan expects trade execution from the backtest node, this becomes a correctness issue.

**Fix**

- Explicitly set `trade_execution=True` (or `False` with documented intent) in `config_builder.py`.
- Add a NautilusTrader version alignment test that fails on major/minor version drift.
- Plan a v1.224+ upgrade with explicit migration checklist.

#### HIGH-2 — `TestJobRecord` / `TestResultRecord` Pydantic models collide with pytest class collection

**Evidence**

- `packages/workflow_spine/models.py:63` defines `class TestJobRecord(BaseModel)`.
- `packages/workflow_spine/models.py:82` defines `class TestResultRecord(BaseModel)`.
- Pytest raises `PytestCollectionWarning` because classes starting with `Test` have `__init__` constructors.

**Risk**

While currently warnings-only, this can mask real test collection failures or cause confusing test discovery behavior. Future pytest versions may escalate this to an error.

**Fix**

- Rename to `JobRecord` / `ResultRecord` (they are not test classes) or prefix with a non-`Test` name like `WorkflowJobRecord`.

#### HIGH-3 — Legacy fixture ref bypass in promotions service

**Evidence**

- `packages/promotions/service.py:16-20` accepts `allow_legacy_fixture_refs=True` (default).
- `services/api/routes/promotions.py:23` passes `allow_legacy_fixture_refs=not strict_evidence`.
- When `strict_evidence` is not requested (default), legacy unscoped fixture refs pass through promotion validation.

**Risk**

Non-strict promotion requests can reference artifacts that lack proper scope lineage. This weakens the evidence chain for promotion decisions.

**Fix**

- Flip default to `allow_legacy_fixture_refs=False`.
- Add deprecation warning when legacy refs are used.
- Require `strict_evidence=True` for all non-dev promotion paths.

### MEDIUM (7)

#### MEDIUM-1 — `.env.execution.local` contains test credentials in repo root

**Evidence**

- `.env.execution.local` contains `BINANCE_API_KEY=test-binance-key` and `BINANCE_API_SECRET=test-binance-secret`.
- `.gitignore` excludes `.env.*` but this file is present on disk.
- The `LocalEnvCredentialSlotStore` writes credentials to this file with `chmod 600`.

**Risk**

While gitignored and chmod-restricted, the file contains plaintext secrets on disk. If the repo root is ever shared or deployed without proper gitignore, secrets leak.

**Fix**

- Consider storing only SHA-256 fingerprints in the slot ref, not the actual values.
- Add a `test-binance-key` detection in the credential store that refuses to write obviously-fake test values.
- Document that `.env.execution.local` is local-dev-only and must not exist in production.

#### MEDIUM-2 — AI builder prompt rejection is case-insensitive but only checks top-level prompt text

**Evidence**

- `packages/ai_builder/service.py:_reject_forbidden_prompt()` checks `prompt.lower()` for "submit order", "api_key", etc.
- The provider response is validated through `validate_strategy_spec()` which does recursive forbidden-reference walking.
- But the prompt guard itself doesn't recursively check nested prompt structures if the provider accepts structured prompts.

**Risk**

Low — the downstream validation catches most cases. But the prompt guard should be consistent with the downstream recursive check.

**Fix**

- Keep as-is but document that the prompt guard is a first-pass filter and the recursive `validators.py` is the authoritative enforcement layer.

#### MEDIUM-3 — `nautilus_rule_graph/strategy.py` imports full NT Strategy class for placeholder

**Evidence**

- `packages/nautilus_rule_graph/strategy.py` imports `nautilus_trader.trading.strategy.Strategy` and creates a concrete subclass.
- This package is described as "placeholder strategy classes/profiles".

**Risk**

If `nautilus_trader` is not installed (e.g., in a lightweight API-only deployment), importing this module will fail.

**Fix**

- Guard the import behind `try/except ImportError` or use a protocol/class instead of importing the real Strategy.
- Document that `nautilus_rule_graph` requires `nautilus_trader` to be installed.

#### MEDIUM-4 — `execution_lane/sessions.py` hardcodes Binance as the only adapter

**Evidence**

- `packages/execution_lane/sessions.py:386-389` imports Binance-specific adapter configs and factories inside the session builder.
- No adapter registry lookup — Binance is the only supported venue for execution lane sessions.

**Risk**

Cannot create paper/live sessions for any venue other than Binance without code changes.

**Fix**

- Route adapter config/factory resolution through `packages/adapter_registry/` instead of direct Binance imports.
- Make the session builder adapter-agnostic with a factory lookup.

#### MEDIUM-5 — No DataTester/ExecTester evidence requirement in backtest runner

**Evidence**

- `packages/backtest_runner/` has smoke tests and catalog replay, but no DataTesterConfig or ExecTesterConfig integration.
- The execution lane requires `data_tester_evidence_ref`, `exec_tester_evidence_ref`, and `reconciliation_evidence_ref` in the profile — but there's no code that actually produces or validates these references.

**Risk**

The execution lane correctly gates on these evidence refs being non-blank, but nothing in the Builder repo actually runs or validates real DataTester/ExecTester evidence. The refs would need to come from an external source or the Daedalus repo.

**Fix**

- Document that DataTester/ExecTester evidence production is out of scope for Builder (belongs in Daedalus or the adapter's own test suite).
- Consider adding a stub/mock evidence generator for end-to-end integration testing.

#### MEDIUM-6 — No explicit `reconciliation_lookback_mins` minimum enforcement in config contract

**Evidence**

- `packages/execution_lane/nautilus_runtime.py:_config_contract()` uses `max(60, profile.reconciliation_lookback_mins)` for the config contract, which is correct.
- But `packages/execution_lane/models.py` may accept `reconciliation_lookback_mins` values below 60 at the Pydantic model level.

**Risk**

A profile with `reconciliation_lookback_mins=10` would be accepted by the model but clamped to 60 by the config builder. The discrepancy is handled but not surfaced to the operator.

**Fix**

- Add a Pydantic validator that enforces `reconciliation_lookback_mins >= 60` at the model level with a clear error message.

#### MEDIUM-7 — Frontend E2E tests depend on Playwright browser installation

**Evidence**

- `apps/web/e2e/builder-shell.spec.ts` requires Chromium installed via `npx playwright install chromium`.
- The current environment doesn't have browsers installed, so E2E tests were skipped in prior reviews.
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

#### LOW-3 — `runtime_label` in `NautilusTradingNodeRuntimePlan` is hardcoded string

**Evidence**

- `packages/execution_lane/nautilus_runtime.py:31` uses `Literal["python_live_integration_specific"]`.
- The value is an informational label, not a runtime switch, but the naming is verbose.

**Fix**

- Consider shortening to `"python_integration"` or documenting why the full label is needed.

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

- The pinned `nautilus_trader==1.223.0` is 3 minor versions behind the latest v1.226.
- Builder should plan an explicit upgrade with a migration checklist that covers: `BacktestVenueConfig.trade_execution`, adapter config API changes, `InstrumentProvider` method changes.
- The reference Daedalus repo is also pinned at v1.223.0, so both repos should upgrade in lockstep.

### WATCH-2 — Execution lane couples Builder to a specific adapter (Binance)

- The current session builder only knows about Binance. As the adapter registry grows, this will need generalization.
- The adapter registry package exists but isn't wired to the execution lane session builder.

### WATCH-3 — DataTester/ExecTester evidence is architecturally external

- Builder correctly gates on evidence refs but doesn't produce them.
- This is by design (Builder is authoring, not testing), but the boundary should be explicit in docs.

## Legacy / Deprecation Inventory

| Item | Location | Status | Action |
|---|---|---|---|
| Legacy compile hash | `services/api/routes/backtest_jobs.py:268` | Active backward-compat | Document + deprecation timeline |
| Legacy fixture refs | `packages/promotions/service.py:16` | Active with `allow_legacy_fixture_refs=True` default | Flip default to `False` |
| Legacy storage schema alias | `packages/workflow_spine/storage_config.py` | Accepted without `shadow_field` | Document + deprecation timeline |
| `TestJobRecord` naming | `packages/workflow_spine/models.py:63` | Causes pytest warnings | Rename |
| `TestResultRecord` naming | `packages/workflow_spine/models.py:82` | Causes pytest warnings | Rename |
| NautilusTrader v1.223.0 pin | `pyproject.toml:7` | 3 versions behind | Plan upgrade |

## Synthesis

- **code-reviewer recommendation:** COMMENT
- **architect status:** WATCH
- **final recommendation:** COMMENT

Address HIGH-1 (NautilusTrader version alignment), HIGH-2 (model naming), and HIGH-3 (legacy fixture bypass) before treating the codebase as merge-ready for a significant release.

## Master reconciliation — catalog-backed Nautilus replay

The `catalog_backed_replay_smoke` smoke test validates BacktestNode catalog replay using synthetic historical quote ticks. This is a wiring and data-flow check — not full trading-production readiness.
