# Nautilus Builder Deep Review Findings

**Review date:** 2026-05-29
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

---

## CRITICAL (0)

None found.

---

## HIGH (3)

### H1. NT version mismatch with Daedalus
**File:** `pyproject.toml:nautilus_trader==1.223.0`
**Category:** NT Alignment
**Risk:** Builder (1.223.0) and Daedalus (1.227.0) are 4 versions apart. If Daedalus produces compile artifacts or strategy specs using 1.227.0 features, Builder may fail to validate or round-trip them. The `adapter_config_builders.py` imports from `nautilus_trader.adapters.binance.*` may break if NT changes adapter APIs between versions.
**Fix:** Upgrade Builder to 1.227.0 and run full test suite. Verify `BinanceDataClientConfig`, `BinanceExecClientConfig`, and `BinanceInstrumentProviderConfig` signatures haven't changed.

### H2. Legacy fixture fallback allows result_id="res_001" without evidence
**File:** `services/api/routes/workflow_results.py:49-51`
**Category:** Bugs
**Risk:** `workflow_result_payload` falls back to fixture data when `result_id == "res_001"` and `allow_fixture_fallback=True` (default). This means any request for `res_001` returns fabricated data with `evidence_mode: "fixture_dev_only"` instead of a 404. In production, this could mask missing real results.
**Fix:** Default `allow_fixture_fallback=False` in production routes. Only enable in dev/test via explicit environment flag.

### H3. Adapter config builder hardcoded to Binance only
**File:** `packages/execution_lane/adapter_config_builders.py:97-99`
**Category:** Architecture
**Risk:** `_ADAPTER_CONFIG_BUILDERS` only has entries for `"BINANCE"` and `"BINANCE_PERP"`. All other adapter IDs fall through to `generic_client_config_builder` which returns empty `LiveDataClientConfig()` with no credentials or factories. This means paper trading sessions for non-Binance adapters silently fail or connect without auth.
**Fix:** Add adapter config builders for OKX, Bybit, and other venues from the adapter registry. Validate that `generic_client_config_builder` at least raises a clear error when credentials are missing.

---

## MEDIUM (10)

### M1. `list_results` has no pagination or limit
**File:** `packages/workflow_spine/repository.py:56-57`, `packages/workflow_spine/postgres_repository.py`
**Category:** Architecture
**Risk:** `list_results()` returns all results without limit or offset. With production data, this could return millions of rows, causing memory pressure and slow response times.
**Fix:** Add `limit` and `offset` parameters. Default to `limit=100`. Add query parameter support in the API route.

### M2. Missing `created_at` timestamp in `WorkflowResultRecord`
**File:** `packages/workflow_spine/models.py:WorkflowResultRecord`
**Category:** Bugs
**Risk:** The model has no timestamp field. `list_results_payload` uses `r.result_id` as `created_at` as a workaround (noted with TODO comment). This means results cannot be sorted or filtered by time.
**Fix:** Add `created_at: str` field to `WorkflowResultRecord` with a default factory. Run migration on existing data.

### M3. `runtime_label: Literal["python_live_integration_specific"]` is verbose and not extensible
**File:** `packages/execution_lane/nautilus_runtime.py:37`
**Category:** Maintainability
**Risk:** The `runtime_label` field uses a `Literal` type that's tightly coupled to the current Python TradingNode implementation. When Rust LiveNode support is added, this field can't be extended without a migration.
**Fix:** Change to `runtime_label: str` with a validator that checks against a known set of labels. This allows adding `"rust_live_node"` without breaking the model.

### M4. Frontend api.test.ts still has network-dependent tests
**File:** `apps/web/lib/api.test.ts`
**Category:** Maintainability
**Risk:** Several tests (lines 162-280) make assertions about full HTTP request/response cycles with mock `fetch`. The test for "posts to the backend-owned BacktestNode run route" expects the URL format `http://127.0.0.1:8000/api/...` but the mock only matches relative paths, causing failures when run from repo root instead of `apps/web/`.
**Fix:** Either exclude `api.test.ts` from vitest when run from root, or always run from `apps/web/`. Consider using a test helper that normalizes URL matching.

### M5. Dockerfile.api doesn't copy all necessary files
**File:** `Dockerfile.api`
**Category:** Bugs
**Risk:** The Dockerfile copies `packages/` and `services/` but doesn't copy `pyproject.toml` dependency list properly (uses `pip install` with hardcoded packages instead of `uv sync`). It also copies `.env.execution.local` which shouldn't be in the image.
**Fix:** Use multi-stage build. Copy `pyproject.toml` + `uv.lock` and use `uv sync`. Remove `.env.execution.local` copy — use env vars from `docker-compose.yml` instead.

### M6. No database migration strategy for production
**File:** `packages/workflow_spine/postgres_repository.py`
**Category:** Architecture
**Risk:** The Postgres repository uses raw SQL with `execute` for schema creation (`workflow_schema_statements`). There's no migration framework (Alembic, etc.) for schema evolution. Adding the `created_at` column (M2) would require manual DDL.
**Fix:** Add Alembic or a lightweight migration runner. Version the schema statements.

### M7. `ai_slop_cleaner` quality gate runs without regression lock
**File:** Quality gate process (not a file)
**Category:** Maintainability
**Risk:** The ultragoal quality gate ran the ai-slop-cleaner as a manual review pass without first locking behavior with regression tests. This is acceptable for the current scope but won't scale.
**Fix:** For future passes, create targeted regression tests for cleaned components before running cleanup.

### M8. `allow_legacy_fixture_refs` deprecation path is incomplete
**File:** `services/api/routes/promotions.py:22-25`
**Category:** Maintainability
**Risk:** The deprecation warning is just a log message. There's no enforcement timeline, no metrics, and no config toggle to hard-disable it after the 2026-07-01 date mentioned in `storage_config.py`.
**Fix:** Add a config flag `ALLOW_LEGACY_FIXTURE_REFS` that defaults to `True` in dev and `False` in production. Add a hard cutoff date that raises after 2026-07-01.

### M9. Daedalus Telegram aiogram-dialog menus not referenced in Builder
**File:** Cross-repo alignment
**Category:** NT Alignment
**Risk:** Daedalus has a full `aiogram-dialog` Telegram gateway (`nautilus_runtime/live/telegram_gateway/ui_dialogs.py`) with signal delivery menus. Builder has no awareness of this integration surface. If Builder produces strategy specs that Daedalus executes, there's no contract connecting Builder's strategy lifecycle to Daedalus's Telegram notification menus.
**Fix:** Document the Builder → Daedalus → Telegram notification boundary. Consider adding a `notification_config` field to `ExecutionLaneProfile` that references Daedalus's signal delivery dialog.

### M10. Custom DEX adapters in Daedalus have no Builder-side registry entries
**File:** `packages/adapter_registry/` vs `Nautilus-Daedalus/crates/adapters/`
**Category:** NT Alignment
**Risk:** Daedalus has 11 custom adapters (apex_omni, paradex, ethereal, grvt, etc.) in Rust. Builder's adapter registry has no entries for these. If an operator creates a strategy targeting one of these venues in Builder, the execution lane can't resolve it.
**Fix:** Add adapter profiles for Daedalus-supported venues to `packages/adapter_registry/`. Consider auto-generating from Daedalus's `Cargo.toml` workspace members.

---

## LOW (8)

### L1. `Dockerfile.api` copies `.env.execution.local`
**File:** `Dockerfile.api:14`
**Category:** Security
**Risk:** Copies `.env.execution.local` into the Docker image. While the file is gitignored and should be empty in CI, this is an unnecessary surface.
**Fix:** Remove the COPY line. Use `environment:` in `docker-compose.yml` instead.

### L2. AntD `Space` deprecation warnings in tests
**File:** `apps/web/components/dashboard/BuilderDashboard.test.tsx` (stderr)
**Category:** Maintainability
**Risk:** AntD v6 deprecated `direction` prop on `Space` in favor of `orientation`. This causes noisy warnings in test output.
**Fix:** Replace `direction="vertical"` with `orientation="vertical"` in all `Space` components.

### L3. `__all__` exports incomplete in several packages
**File:** Multiple `__init__.py` files
**Category:** Maintainability
**Risk:** Some packages export a subset of their public API in `__all__`, making it unclear what's intended as public vs internal.
**Fix:** Audit all `__init__.py` files for complete `__all__` exports.

### L4. `npx vitest run` from repo root fails (JSX parse errors)
**File:** Project root vs `apps/web/`
**Category:** Maintainability
**Risk:** `vitest.config.mts` lives in `apps/web/` but not at repo root. Running `npx vitest run` from repo root causes JSX parse failures because the config isn't found. This confused the initial ultragoal resume.
**Fix:** Add a root-level `vitest.config.ts` that delegates to `apps/web/vitest.config.mts`, or document that vitest must run from `apps/web/`.

### L5. `BuilderDashboard.test.tsx` uses `screen.getByText(/Strategy Builder/)` which is fragile
**File:** `apps/web/components/dashboard/BuilderDashboard.test.tsx:47`
**Category:** Maintainability
**Risk:** Tests use regex text matching which breaks if button labels change.
**Fix:** Use `data-testid` attributes for stable test selectors.

### L6. No health check endpoint in Dockerfile.api
**File:** `Dockerfile.api`
**Category:** Maintainability
**Risk:** No HEALTHCHECK instruction. Docker/K8s can't monitor API health.
**Fix:** Add `HEALTHCHECK CMD curl -f http://localhost:8000/health || exit 1`.

### L7. `storage_config.py` deprecated legacy alias has no migration path
**File:** `packages/workflow_spine/storage_config.py:1-2`
**Category:** Legacy/Deprecation
**Risk:** The DEPRECATED comment says "legacy alias will be removed after 2026-07-01" but there's no migration tooling or tracking issue.
**Fix:** Create a tracking issue. Add a runtime warning when the legacy alias is used.

### L8. Backtest `legacy_hash` derivation in `backtest_jobs.py`
**File:** `services/api/routes/backtest_jobs.py:267-272`
**Category:** Legacy/Deprecation
**Risk:** DEPRECATED legacy compile hash derivation is still executed. The comment says "removed after 2026-07-01" but there's no feature flag to disable it.
**Fix:** Add a `USE_LEGACY_COMPILE_HASH` env flag. Default `False` in production.

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
| Legacy fixture fallback | `workflow_results.py:res_001` | Active | None | Gate behind env flag |
| Legacy compile hash | `backtest_jobs.py:267` | Deprecated | 2026-07-01 | Remove after migration |
| `allow_legacy_fixture_refs` | `promotions/service.py` | Deprecated | None | Add hard cutoff |
| `TestJobRecord`/`TestResultRecord` naming | `workflow_spine/models.py` | Resolved | Done | Already renamed to `WorkflowJobRecord`/`WorkflowResultRecord` |
| `shadow_candidate` lifecycle status | `lifecycle/models.py` | Resolved | Done | Removed in commit `cee5d03` |
| Block Canvas UI | `apps/web/` | Resolved | Done | Removed in commit `182a419` |

---

## Review verdict

- **code-reviewer recommendation:** COMMENT
- **architect status:** WATCH
- **final recommendation:** COMMENT

Address H1 (NT version upgrade), H2 (fixture fallback), and H3 (adapter registry) before production readiness. MEDIUM items should be tracked for near-term resolution.
