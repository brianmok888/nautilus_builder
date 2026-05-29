# Nautilus Builder Deep Review Findings

**Review date:** 2026-05-29 (full deep review v2)
**Review scope:** Full codebase (packages/ + services/ + apps/web/ + tests/)
**Reference:** NautilusTrader 1.227.0, Daedalus execution authority, aiogram-dialog patterns
**Method:** Static analysis (AST scan, grep), manual code review, test verification, cross-repo alignment check, legacy/deprecation inventory

---

## Summary

| Category | CRITICAL | HIGH | MEDIUM | LOW | INFO |
|----------|----------|------|--------|-----|------|
| Security | 0 | 1 | 2 | 2 | 1 |
| Bugs | 0 | 0 | 1 | 1 | 0 |
| Architecture | 0 | 0 | 2 | 1 | 1 |
| Maintainability | 0 | 0 | 2 | 3 | 1 |
| NT Alignment | 0 | 0 | 0 | 1 | 1 |
| Legacy/Deprecation | 0 | 0 | 1 | 2 | 0 |
| **Total** | **0** | **1** | **8** | **10** | **4** |

### Fix status

| ID | Title | Status |
|----|-------|--------|
| H1 | ~~NT version mismatch with Daedalus~~ | **FIXED** (S3) |
| H2 | ~~Legacy fixture fallback without evidence~~ | **FIXED** (S1) |
| H3 | ~~Adapter config builder hardcoded to Binance~~ | **FIXED** (S2) |
| H4 | Default dev token in docker-compose fallback | **NEW** — HIGH |
| M1 | ~~`list_results` has no pagination~~ | **FIXED** (S4) |
| M2 | ~~Missing `created_at` timestamp~~ | **FIXED** (S4) |
| M3 | ~~`runtime_label` not extensible~~ | **FIXED** (S3) |
| M4 | Frontend api.test.ts network-dependent tests | Open |
| M5 | `list_results_payload` API route ignores pagination params | **NEW** — Open |
| M6 | `_client_configs` silently swallows adapter registry ValueError | **NEW** — Open |
| M7 | ~~`execution_authority` not enforced at compile time~~ | **FIXED** |
| M8 | SqliteWorkflowRepository named PostgresWorkflowRepository | **NEW** — Open |
| M9 | Dockerfile.api COPY .env.execution.local may fail on fresh clone | **NEW** — Open |
| M10 | Postgres port exposed in docker-compose | **NEW** — Open |
| L1 | `storage_config.py` legacy alias no migration path | Open |
| L2 | Backtest `legacy_hash` derivation | Open |
| L3 | Frontend test selectors fragile | Open |
| L4 | `__all__` exports incomplete | Open |
| L5 | ~~No health check in Dockerfile~~ | **FIXED** |
| L6 | `created_at` uses `__import__` in default_factory | **NEW** — Open |
| L7 | No API rate limiting | **NEW** — Open |
| L8 | No CORS middleware | **NEW** — Open |
| L9 | `NEXT_PUBLIC_BUILDER_API_TOKEN` in client bundle | **NEW** — Open |
| L10 | InMemory dicts unbounded in service classes | **NEW** — Open |

---

## CRITICAL (0)

None found.

---

## HIGH (1)

### H4. Default dev token in docker-compose fallback
**File:** `docker-compose.yml:27,46`
**Category:** Security
**Risk:** `BUILDER_API_TOKEN: ${BUILDER_API_TOKEN:-dev-token}` and `NEXT_PUBLIC_BUILDER_API_TOKEN: ${BUILDER_API_TOKEN:-dev-token}` provide a fallback token that is trivially guessable. If deployed without overriding `BUILDER_API_TOKEN`, the API is accessible with `dev-token`.
**Fix:** Remove the default fallback. Require explicit `BUILDER_API_TOKEN` env var in production. Add startup check that rejects `dev-token` when `APP_ENV=production`.
**Priority:** HIGH — easy to miss in deployment.

---

## MEDIUM (8)

### M4. Frontend api.test.ts still has network-dependent tests
**File:** `apps/web/lib/api.test.ts:162-280`
**Category:** Maintainability
**Risk:** Several tests make real fetch calls to localhost. CI environments may not have the API running, causing flaky test failures.
**Fix:** Use `vi.fn()` mocks for all fetch calls, or gate network tests behind an env flag.

### M5. `list_results_payload` API route ignores pagination params
**File:** `services/api/routes/workflow_results.py:91-105`
**Category:** Bugs
**Risk:** `list_results_payload` calls `repository.list_results()` without passing `limit` or `offset` from the request. The repository supports pagination but the API route doesn't expose it.
**Fix:** Accept `limit` and `offset` query parameters and pass them through. Default `limit=100`.

### M6. `_client_configs` silently swallows adapter registry ValueError
**File:** `packages/execution_lane/sessions.py:389-396`
**Category:** Architecture
**Risk:** When `get_adapter_profile(adapter_id)` raises `ValueError` (unknown adapter), the exception is silently caught with `pass`. This means an unregistered adapter silently falls through to `generic_client_config_builder`, which may create an empty config. The user gets no feedback that their adapter wasn't found.
**Fix:** Log a warning when adapter is not in registry. Consider whether silent fallback to generic builder is the intended behavior for MVP or should be an error.

### M8. SqliteWorkflowRepository aliased as PostgresWorkflowRepository
**File:** `packages/workflow_spine/postgres_repository.py:183`
**Category:** Maintainability
**Risk:** `PostgresWorkflowRepository = SqliteWorkflowRepository` is a misleading alias. The class doesn't use Postgres at all — it uses SQLite. This can confuse contributors who expect real Postgres queries.
**Fix:** Rename to `SqliteWorkflowRepository` everywhere. Add a real Postgres implementation when needed, or remove the alias.

### M9. Dockerfile.api COPY .env.execution.local may fail on fresh clone
**File:** `Dockerfile.api:11`
**Category:** Architecture
**Risk:** `COPY .env.execution.local .env.local` will fail if the file doesn't exist (fresh clone without setup). This breaks `docker build` for new developers.
**Fix:** Create an empty `.env.execution.local` during setup, or use a conditional COPY / multi-stage build pattern.

### M10. Postgres port exposed in docker-compose
**File:** `docker-compose.yml:12`
**Category:** Security
**Risk:** `"5432:5432"` exposes Postgres to the host network. Combined with the default `builder_dev` password, this is a security concern in shared environments.
**Fix:** Bind to `127.0.0.1:5432:5432` for local-only access, or remove port exposure entirely (only API service needs DB access).

### M11. Docker compose default Postgres password
**File:** `docker-compose.yml:9`
**Category:** Security
**Risk:** `POSTGRES_PASSWORD: builder_dev` is hardcoded in docker-compose.yml. While acceptable for local dev, the comment should explicitly state this is dev-only and must be changed for production.
**Fix:** Use `${POSTGRES_PASSWORD:-builder_dev}` and document the production override.

---

## LOW (10)

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

### L6. `created_at` uses `__import__("datetime")` in default_factory
**File:** `packages/workflow_spine/models.py:92`
**Category:** Maintainability
**Risk:** `__import__("datetime")` in a default_factory is an anti-pattern that bypasses the module-level import system. It also triggers `RAW_CODE_PATTERNS` detection if scanned broadly.
**Fix:** Import `datetime` at module level and use `default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat()`.

### L7. No API rate limiting
**File:** `services/api/fastapi_app.py`
**Category:** Security
**Fix:** Add slowapi or similar rate limiting middleware for production.

### L8. No CORS middleware
**File:** `services/api/fastapi_app.py`
**Category:** Security
**Fix:** Add `CORSMiddleware` with configurable origins if direct browser access is needed.

### L9. `NEXT_PUBLIC_BUILDER_API_TOKEN` visible in client bundle
**File:** `apps/web/lib/api.ts:94-95`, `docker-compose.yml:46`
**Category:** Security
**Fix:** For production, prefer server-side API proxy with `BUILDER_API_TOKEN` (non-public) and remove `NEXT_PUBLIC_BUILDER_API_TOKEN`.

### L10. InMemory dicts unbounded in service classes
**File:** `packages/execution_lane/service.py:17-23`, `packages/strategy_spec/repository.py:10-11`, `packages/strategy_registry/service.py:68`
**Category:** Maintainability
**Risk:** Service classes use plain `dict` for storage with no eviction. In long-running processes, these grow without bound.
**Fix:** For MVP with InMemory stores this is acceptable. Document that Postgres migration is required for production scaling.

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
| `allow_legacy_fixture_refs` | `promotions/service.py` | Deprecated | 2026-07-01 | Add hard cutoff |
| `PostgresWorkflowRepository` alias | `workflow_spine/postgres_repository.py:183` | Deprecated | 2026-07-01 | Rename to SqliteWorkflowRepository |
| `TestJobRecord`/`TestResultRecord` naming | `workflow_spine/models.py` | Resolved | Done | Already renamed |
| `shadow_candidate` lifecycle status | `lifecycle/models.py` | Resolved | Done | Removed in commit `cee5d03` |
| Block Canvas UI | `apps/web/` | Resolved | Done | Removed in commit `182a419` |

---

## Master reconciliation — catalog-backed Nautilus replay

- `catalog_backed_replay_smoke` runs synthetic historical quote ticks through the full BacktestNode pipeline.
- This is a wiring and data-flow check — not full trading-production readiness.
- Master reconciliation evidence appears in all three review docs (structure, findings, handguard).

---

## Architectural Status: WATCH

### Concern 1: InMemory stores have no production migration path
The codebase uses `InMemoryWorkflowRepository`, `InMemoryStrategyRepository`, and in-memory service dicts throughout. Postgres is wired for strategies and adapters but not for workflow spine, execution lane, or runtime events. Production readiness requires completing the Postgres migration for all stores.

### Concern 2: Adapter fallback in sessions.py
`_client_configs` silently falls back from a registry lookup to `generic_client_config_builder`. This is architecturally questionable for production — an unregistered adapter should probably fail explicitly rather than silently connecting with empty config.

### Concern 3: Frontend token in NEXT_PUBLIC env var
The API token is exposed to the browser via `NEXT_PUBLIC_BUILDER_API_TOKEN`. This is acceptable for VM-deployed operator tools but would be a security concern if deployed as a public-facing web app.

---

## Review verdict

- **code-reviewer recommendation:** COMMENT
- **architect status:** WATCH
- **final recommendation:** COMMENT

**Remaining HIGH:** H4 (default dev token) — easy fix, not blocking.
**Remaining MEDIUM:** M4, M5, M6, M8, M9, M10, M11 — all non-blocking but should be addressed before production deployment.

**Test evidence:** 442 pytest tests passing, 0 compilation errors.
