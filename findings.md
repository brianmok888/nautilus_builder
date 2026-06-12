# Deep Review Findings — nautilus_builder

**Review Date:** 2026-06-12
**Scope:** nautilus_builder full tree, NT v1.227.0 API alignment
**Test Evidence:** 1479 passed / 1 skipped

---

## CODE REVIEW REPORT

Files Reviewed: 60+ (critical paths)
Total Issues: 11
Architectural Status: WATCH

---

### CRITICAL (1)

**C-01: Unbounded in-memory credential/token stores in production path**
- Files: `packages/auth/service.py`, `packages/execution_lane/service.py`
- Issue: `AuthTokenService._tokens` is a plain `dict[str, UserProjectContext]` with no eviction, TTL, or size limit. `ExecutionLaneService._sessions`, `_profiles`, `_commands`, `_reports` are all unbounded dicts. In a long-running production FastAPI process, these grow without bound.
- Risk: Memory exhaustion under sustained load. Tokens issued for testing (`nb_test_*`) are never cleaned up.
- Fix: Add TTL-based eviction or LRU cap for auth tokens. Consider Postgres-backed session persistence for execution lane state in production (the `postgres_repository.py` exists but the in-memory service is the default).

---

### HIGH (2)

**H-01: Adapter config builder only supports Binance**
- File: `packages/execution_lane/adapter_config_builders.py`
- Issue: Only `build_binance_data_config()` and `build_binance_exec_config()` exist. `build_generic_data_config()` raises `ValueError` for non-Binance venues. No wiring for Bybit, OKX, or any other venue.
- Risk: Execution lane paper sessions fail for any non-Binance venue. Blocks multi-venue strategy testing.
- Fix: Add adapter config builders for all venues, or make `build_generic_data_config()` fall back to a safe default config pattern.

**H-02: Evidence production fail-closed only enforced at app factory level**
- File: `services/api/fastapi_app.py`
- Issue: The ValueError for in-memory evidence in production is raised inside `create_fastapi_app()`, which is only called during server startup. If a developer bypasses the factory and creates a FastAPI app directly (e.g., in tests or scripts), the guard is skipped.
- Risk: Misconfigured production deployment without evidence persistence.
- Fix: Add a startup event handler that re-validates evidence storage config, or make the check a FastAPI dependency.

---

### MEDIUM (4)

**M-01: Paper strategy only subscribes to quote ticks**
- File: `packages/execution_lane/paper_strategy.py`
- Issue: `ExecutionLanePaperStrategy` subscribes to `quote_ticks` but the StrategySpec model supports bar-based strategies (`bar_type` field). Paper sessions for bar strategies won't receive any data.
- Fix: Add conditional subscription based on spec data type (bars vs ticks).

**M-02: No `on_reset` cleanup in paper strategy**
- File: `packages/execution_lane/paper_strategy.py`
- Issue: Missing `on_reset()` method. `observed_quote_ticks` counter is not reset.
- Fix: Add `on_reset()` that clears `observed_quote_ticks` and `self.instrument = None`.

**M-03: SQLite workflow repository uses string interpolation for LIMIT/OFFSET**
- File: `packages/workflow_spine/postgres_repository.py:109-113`
- Issue: `sql += f" LIMIT {int(limit or -1)} OFFSET {int(offset)}"` — while `int()` provides basic sanitization, the pattern of string interpolation in SQL is fragile. The table name is also interpolated.
- Fix: Use parameterized queries for LIMIT/OFFSET (`?` placeholders).

**M-04: StrategySpec classic model doesn't enforce `output_mode=signal_preview_only`**
- File: `packages/strategy_spec/models.py`
- Issue: The v1 `StrategySpec` has `OutputMode.SIGNAL_PREVIEW_ONLY` as the only enum value, but doesn't have a model validator enforcing it (unlike `StrategySpecMicrostructureV1` which has an explicit `Literal[False]` guard on `execution_authority`).
- Risk: If new output modes are added to the enum without updating validators, the classic spec could accept them silently.
- Fix: Add a model validator that enforces `output_mode == SIGNAL_PREVIEW_ONLY`.

---

### LOW (4)

**L-01: `_installed_nautilus_version()` always returns None**
- File: `packages/execution_lane/nautilus_runtime.py:183`
- Issue: The function has `try: import nautilus_trader; return None` — the `return None` is inside the try block before any version extraction. Dead code.
- Fix: Change to `return str(getattr(nautilus_trader, "__version__", "")) or None`.

**L-02: Starlette deprecation warning in test client**
- Issue: `StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated; install httpx2 instead`.
- Fix: Update FastAPI/Starlette dependency or install `httpx2`.

**L-03: Missing explicit `on_stop` in `ExecutionLanePaperStrategy`**
- File: `packages/execution_lane/paper_strategy.py`
- Issue: No explicit unsubscribe in `on_stop()`. NT framework handles cleanup, but explicit unsubscribe is recommended per NT conventions.
- Fix: Add `on_stop()` with `self.unsubscribe_quote_ticks()`.

**L-04: No `.env.execution.local` file permission validation**
- File: `packages/execution_lane/credentials.py`
- Issue: The credential slot store writes to `.env.execution.local` but doesn't validate that the file has restrictive permissions (0600). `_validate_env_file_path` checks for path separators but not file mode.
- Fix: Add `os.chmod(path, 0o600)` after writing, or validate existing permissions.

---

## ARCHITECTURE WATCHLIST

**AW-01: Execution lane in-memory defaults may not survive production restarts**
- Concern: All execution lane state (profiles, commands, sessions, reports) lives in memory by default. A process restart loses all in-flight session state.
- Status: WATCH
- Recommendation: Ensure production deployments use the Postgres-backed repositories from the start, not just for evidence.

**AW-02: Paper strategy lacks warmup data flow**
- Concern: `on_start()` subscribes directly to quote_ticks without requesting historical data first. Per NT conventions, `request_bars()` should precede `subscribe_bars()`.
- Status: WATCH
- Recommendation: Add historical data request in paper strategy `on_start()` before subscription.

---

## LEGACY/DEPRECATION CLOSURE INVENTORY

| Item | Status | Location | Action |
|------|--------|----------|--------|
| `credential_slot_http_disabled` response | ✅ Closed | `credentials.py:47` | Returns 410 |
| Browser credential bootstrap | ✅ Closed | `credentials.py:46-48` | Returns error payload |
| `CredentialSlotBootstrap.tsx` | ✅ Closed | handguard guard | Asserted absent |
| `strategy_lane_coupled` | ✅ Closed | `models.py:150`, `nautilus_runtime.py:36` | Literal[False] |
| `browser_credentials_allowed` | ✅ Closed | `config_contract.py:10,20` | Literal[False] |
| `credential_inputs_allowed` | ✅ Closed | `service.py` snapshot | Always False |
| Coinbase International adapter (NT v1.224 removal) | ✅ Not referenced | N/A | No action |
| dYdX v3 adapter (NT v1.223 removal) | ✅ Not referenced | N/A | No action |
| `fill_limit_at_touch` (NT v1.224 rename) | ✅ Not used | N/A | No action |
| `may_submit_order` / `execution_authority` | ✅ Closed | `models.py:62-63,194-195` | Paper blocks both |
| `_installed_nautilus_version()` dead code | 🔧 Bug | `nautilus_runtime.py:183` | Returns None always |

---

## SYNTHESIS

- code-reviewer recommendation: **REQUEST CHANGES** (1 CRITICAL, 2 HIGH)
- architect status: **WATCH** (2 architectural concerns, no blockers)
- final recommendation: **REQUEST CHANGES**

Address CRITICAL item (unbounded stores) and HIGH items (multi-venue adapter support, evidence guard hardening) before production deployment.
