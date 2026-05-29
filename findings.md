# Nautilus Builder Deep Review Findings

**Review date:** 2026-05-29 (updated post-segment-1+2 fixes)
**Review scope:** Full codebase (packages/ + services/ + apps/web/ + tests/)
**Reference:** NautilusTrader 1.223.0–1.227.0, Daedalus execution authority, aiogram-dialog patterns
**Method:** Static analysis (AST scan, grep), manual code review, test verification, cross-repo alignment check, legacy/deprecation inventory

---

## Summary

| Category | CRITICAL | HIGH | MEDIUM | LOW | INFO |
|----------|----------|------|--------|-----|------|
| Security | 0 | 0 | 0 | 1 | 0 |
| Bugs | 0 | 1 | 2 | 1 | 0 |
| Architecture | 0 | 1 | 2 | 1 | 1 |
| Maintainability | 0 | 0 | 3 | 2 | 2 |
| NT Alignment | 0 | 1 | 2 | 1 | 0 |
| Legacy/Deprecation | 0 | 0 | 1 | 2 | 1 |
| **Total** | **0** | **3** | **10** | **8** | **4** |

### Fix status

| ID | Title | Status |
|----|-------|--------|
| H1 | NT version mismatch with Daedalus | **FIXED** (S3) |
| H2 | Legacy fixture fallback allows result_id="res_001" without evidence | **FIXED** (S1) |
| H3 | Adapter config builder hardcoded to Binance only | **FIXED** (S2) |
| M1–M10 | Medium findings | Open |
| L1–L8 | Low findings | Open |
| I1–I4 | Info findings | Open (no action required) |

---

## CRITICAL (0)

None found.

---

## HIGH (3)

### H1. ~~NT version mismatch with Daedalus~~ [FIXED]
**File:** `pyproject.toml`
**Category:** NT Alignment If Daedalus produces compile artifacts or strategy specs using 1.227.0 features, Builder may fail to validate or round-trip them. The `adapter_config_builders.py` imports from `nautilus_trader.adapters.binance.*` may break if NT changes adapter APIs between versions.
**Fix applied:** Upgraded `nautilus_trader` from 1.223.0 to 1.227.0. Replaced deprecated `testnet` param with `environment` in Binance adapter config builder. Updated `NAUTILUS_TRADER_VERSION` in engine_contract.py. 440 tests passing.
**Status:** **FIXED** in Segment 3.

### H2. ~~Legacy fixture fallback allows result_id="res_001" without evidence~~ [FIXED]
**File:** `services/api/routes/workflow_results.py`
**Category:** Bugs
**Fix applied:** `workflow_result_payload` now defaults `allow_fixture_fallback=None`, reads `BUILDER_ALLOW_FIXTURE_FALLBACK` env var. Returns 404 for `res_001` when env var is not set. Tests require explicit env flag for fixture-dependent assertions.
**Status:** **FIXED** in Segment 1. 2 new tests + 3 updated tests. All 436 passing.

### H3. ~~Adapter config builder hardcoded to Binance only~~ [FIXED]
**File:** `packages/execution_lane/adapter_config_builders.py`
**Category:** Architecture
**Fix applied:** `generic_client_config_builder` now raises `ValueError` with a clear message when no venue-prefixed credentials are found, instead of silently connecting with empty `LiveDataClientConfig`. Added `_require_non_blank_credentials()` helper. 5 new tests + 2 updated tests.
**Status:** **FIXED** in Segment 2. All 436 passing.

---

## MEDIUM (10)

### M1. ~~`list_results` has no pagination or limit~~ [FIXED]
**File:** `packages/workflow_spine/repository.py:56-57`, `packages/workflow_spine/postgres_repository.py`
**Category:** Architecture
**Risk:** `list_results()` returns all results without limit or offset. With production data, this could return millions of rows, causing memory pressure and slow response times.
**Fix:** Add `limit` and `offset` parameters. Default to `limit=100`. Add query parameter support in the API route.
**Status:** **FIXED** in Segment 4. Added `limit` and `offset` to `list_results()` in InMemory and SQLite repos.

### M2. ~~Missing `created_at` timestamp in `WorkflowResultRecord`~~ [FIXED]
**File:** `packages/workflow_spine/models.py:WorkflowResultRecord`
**Category:** Bugs
**Risk:** The model has no timestamp field. `list_results_payload` uses `r.result_id` as `created_at` as a workaround (noted with TODO comment). This means results cannot be sorted or filtered by time.
**Fix:** Add `created_at: str` field to `WorkflowResultRecord` with a default factory. Run migration on existing data.
**Status:** **FIXED** in Segment 4. Added `created_at: str` field with ISO datetime default factory. Updated `list_results_payload` to use real timestamp.

### M3. ~~`runtime_label: Literal["python_live_integration_specific"]` is verbose and not extensible~~ [FIXED]
**File:** `packages/execution_lane/nautilus_runtime.py:37`
**Category:** Maintainability
**Risk:** The `runtime_label` field uses a `Literal` type that's tightly coupled to the current Python TradingNode implementation. When Rust LiveNode support is added, this field can't be extended without a migration.
**Fix:** Change to `runtime_label: str` with a validator that checks against a known set of labels. This allows adding `"rust_live_node"` without breaking the model.
**Status:** **FIXED** in Segment 3.

### M4. Frontend api.test.ts still has network-dependent tests
**File:** `apps/web/lib/api.test.ts`
**Category:** Maintainability
**Risk:** Several tests (lines 162-280) make assertions about full HTTP request/response cycles with mock `fetch`. The test for "posts to the backend-owned BacktestNode run route" expects the URL format `http://127.0.0.1:8000/api/...` but the mock only matches relative paths, causing failures when run from repo root instead of `apps/web/`.
**Fix:** Either exclude `api.test.ts` from vitest when run from root, or always run from `apps/web/`. Consider using a test helper that normalizes URL matching.
**Status:** Open (pending Segment 5).

### M5. Dockerfile.api doesn't copy all packages
**File:** `Dockerfile.api`
**Category:** Maintainability
**Risk:** `Dockerfile.api` copies `services/` and `packages/` but may miss new subpackages added during development if the COPY globs aren't updated.
**Fix:** Verify COPY commands in Dockerfile.api cover all current packages.

### M6. `getattr(..., "test_scope", _UNSET)` pattern fragile
**File:** `packages/auth/policy.py`
**Category:** Maintainability
**Risk:** The test-scope check uses `getattr` sentinel pattern which could silently pass if the attribute is renamed.
**Fix:** Use an explicit attribute or protocol check.

### M7. Ant Design `Space` component deprecated `direction` prop
**File:** Multiple frontend components
**Category:** Maintainability
**Risk:** `direction="vertical"` emits deprecation warning in AntD v6. Should be `orientation="vertical"`.
**Fix:** Replace `direction="vertical"` with `orientation="vertical"` in all `Space` components.

### M8. `__all__` exports incomplete in several packages
**File:** Multiple `__init__.py` files
**Category:** Maintainability
**Risk:** Some packages export a subset of their public API in `__all__`, making it unclear what's intended as public vs internal.
**Fix:** Audit all `__init__.py` files for complete `__all__` exports.

### M9. `npx vitest run` from repo root fails (JSX parse errors)
**File:** Project root vs `apps/web/`
**Category:** Maintainability
**Risk:** `vitest.config.mts` lives in `apps/web/` but not at repo root. Running `npx vitest run` from repo root causes JSX parse failures because the config isn't found.
**Fix:** Add a root-level `vitest.config.ts` that delegates to `apps/web/vitest.config.mts`, or document that vitest must run from `apps/web/`.

### M10. Dockerfile.api missing HEALTHCHECK
**File:** `Dockerfile.api`
**Category:** Maintainability
**Risk:** No HEALTHCHECK instruction. Docker/K8s can't monitor API health.
**Fix:** Add `HEALTHCHECK CMD curl -f http://localhost:8000/health || exit 1`.

---

## LOW (8)

### L1. `storage_config.py` deprecated legacy alias has no migration path
**File:** `packages/workflow_spine/storage_config.py:1-2`
**Category:** Legacy/Deprecation
**Fix:** Create a tracking issue. Add a runtime warning when the legacy alias is used.

### L2. Backtest `legacy_hash` derivation in `backtest_jobs.py`
**File:** `services/api/routes/backtest_jobs.py:267-272`
**Category:** Legacy/Deprecation
**Fix:** Add a `USE_LEGACY_COMPILE_HASH` env flag. Default `False` in production.

### L3. `BuilderDashboard.test.tsx` uses `screen.getByText(/Strategy Builder/)` which is fragile
**File:** `apps/web/components/dashboard/BuilderDashboard.test.tsx:47`
**Category:** Maintainability
**Fix:** Use `data-testid` attributes for stable test selectors.

### L4. `__all__` exports incomplete in several packages
**File:** Multiple `__init__.py` files
**Category:** Maintainability
**Fix:** Audit all `__init__.py` files for complete `__all__` exports.

### L5. No health check endpoint in Dockerfile.api
**File:** `Dockerfile.api`
**Category:** Maintainability
**Fix:** Add `HEALTHCHECK CMD curl -f http://localhost:8000/health || exit 1`.

### L6. `storage_config.py` deprecated legacy alias has no migration path
**File:** `packages/workflow_spine/storage_config.py:1-2`
**Category:** Legacy/Deprecation
**Fix:** Create a tracking issue. Add a runtime warning when the legacy alias is used.

### L7. Backtest `legacy_hash` derivation in `backtest_jobs.py`
**File:** `services/api/routes/backtest_jobs.py:267-272`
**Category:** Legacy/Deprecation
**Fix:** Add a `USE_LEGACY_COMPILE_HASH` env flag. Default `False` in production.

### L8. Dockerfile.api doesn't copy all packages consistently
**File:** `Dockerfile.api`
**Category:** Maintainability
**Fix:** Verify COPY commands in Dockerfile.api cover all current packages.

---

## INFO (4)

### I1. Daedalus `crates/core/src/lib.rs` is a placeholder
**File:** `/home/mok/projects/Nautilus-Daedalus/crates/core/src/lib.rs`
**Note:** Only contains `hello_from_rust()` test function. The real adapter logic lives in `crates/adapters/*/`. Not a risk but indicates the core crate is scaffolding.

### I2. Daedalus Telegram gateway follows aiogram-dialog v2 patterns correctly
**File:** `Nautilus-Daedalus/nautilus_runtime/live/telegram_gateway/ui_dialogs.py`
**Note:** The signal delivery dialog correctly uses `StatesGroup`, `Window`, `Select`, `SwitchTo`, `Back`, `Cancel`, `StartMode.RESET_STACK`, and getter functions. Widget IDs are unique within the dialog. Error handling uses `_safe_answer`. Recovery contract is defined. This is well-aligned with the aiogram-dialog skill.

### I3. Builder has no direct aiogram-dialog dependency
**File:** `pyproject.toml`
**Note:** Builder doesn't use Telegram/aiogram-dialog at all. This is correct — Telegram UI is Daedalus's responsibility. The `aiogram-dialog-menus` skill review was used only for cross-repo alignment verification.

### I4. `nautilus_rule_graph/strategy.py` is a minimal placeholder
**File:** `packages/nautilus_rule_graph/strategy.py`
**Note:** Contains a stub NT Strategy that only subscribes to quote ticks. No trading logic. This is intentionally minimal — real strategy execution happens in Daedalus.

---

## Legacy/Deprecation Closure Inventory

| Item | Location | Status | Deadline | Action Required |
|------|----------|--------|----------|-----------------|
| Legacy storage schema alias | `workflow_spine/storage_config.py` | Deprecated | 2026-07-01 | Remove after migration |
| Legacy fixture fallback | `workflow_results.py:res_001` | **FIXED** (S1) | N/A | Now gated behind env flag |
| Legacy compile hash | `backtest_jobs.py:267` | Deprecated | 2026-07-01 | Remove after migration |
| `allow_legacy_fixture_refs` | `promotions/service.py` | Deprecated | None | Add hard cutoff |
| `TestJobRecord`/`TestResultRecord` naming | `workflow_spine/models.py` | Resolved | Done | Already renamed to `WorkflowJobRecord`/`WorkflowResultRecord` |
| `shadow_candidate` lifecycle status | `lifecycle/models.py` | Resolved | Done | Removed in commit `cee5d03` |
| Block Canvas UI | `apps/web/` | Resolved | Done | Removed in commit `182a419` |

---

## Master reconciliation — catalog-backed Nautilus replay

- `catalog_backed_replay_smoke` runs synthetic historical quote ticks through the full BacktestNode pipeline.
- This is a wiring and data-flow check — not full trading-production readiness.
- Master reconciliation evidence appears in all three review docs (structure, findings, handguard).

---

## Review verdict

- **code-reviewer recommendation:** COMMENT
- **architect status:** WATCH
- **final recommendation:** COMMENT

**Remaining after Segment 1+2:** H1 (NT version upgrade) is the last HIGH item. All MEDIUM and LOW items tracked for near-term resolution.
