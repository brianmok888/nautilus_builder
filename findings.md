# Deep Review Findings — nautilus_builder

**Review Date:** 2026-06-12
**Scope:** nautilus_builder full tree, NT v1.227.0 API alignment
**Test Evidence:** 1512 passed / 1 skipped (2 pre-existing failures)

---

## CODE REVIEW REPORT

Files Reviewed: 60+ (critical paths)
Total Issues: 11
Architectural Status: CLEAR (was WATCH, all WATCH items addressed)

---

### CRITICAL (0) — All resolved

~~**C-01: Unbounded in-memory stores**~~ — **RESOLVED**
- Auth token service now has TTL + LRU eviction (`max_tokens`, `ttl_seconds`)
- Execution lane service now has `max_reports` and `max_sessions` capacity bounds
- Tests: 13 new tests covering eviction and TTL

---

### HIGH (0) — All resolved

~~**H-01: Adapter config builder only supports Binance**~~ — **CONFIRMED ALREADY HANDLED**
- `get_adapter_config_builder()` falls back to `generic_client_config_builder` for any venue
- Generic builder uses NT's `LiveDataClientConfig`/`LiveExecClientConfig` which work with any adapter
- Tests: 5 new tests confirming fallback works for BYBIT, OKX, and unknown venues

~~**H-02: Evidence fail-closed only at app factory**~~ — **RESOLVED**
- Added startup event handler that re-validates evidence storage config
- Guarded with `hasattr(app, "on_event")` for test compatibility
- Tests: 5 new tests covering the startup guard

---

### MEDIUM (0) — All resolved

~~**M-01: Paper strategy only subscribes to quote ticks**~~ — **RESOLVED**
- Added `bar_type` field to `ExecutionLanePaperStrategyConfig`
- `on_start()` conditionally subscribes to bars or quote ticks based on config
- Added `on_bar()` handler with counter
- Tests: 9 new tests

~~**M-02: No on_reset cleanup in paper strategy**~~ — **RESOLVED**
- Added `on_reset()` that clears `instrument`, `observed_quote_ticks`, `observed_bars`

~~**M-03: SQL LIMIT/OFFSET string interpolation**~~ — **RESOLVED**
- Changed to parameterized queries (`?` placeholders) in `postgres_repository.py`

~~**M-04: StrategySpec output_mode enforcement**~~ — **RESOLVED**
- Added `model_validator` on `StrategySpec` enforcing `output_mode == SIGNAL_PREVIEW_ONLY`
- Tests: 3 new tests

---

### LOW (0) — All resolved

~~**L-01: _installed_nautilus_version() always returns None**~~ — **FALSE POSITIVE**
- Code is correct; the earlier review was based on truncated output

~~**L-03: Missing on_stop in paper strategy**~~ — **RESOLVED**
- Added `on_stop()` with explicit `unsubscribe_quote_ticks()` or `unsubscribe_bars()`

~~**L-04: No .env.execution.local file permission validation**~~ — **FALSE POSITIVE**
- `chmod(0o600)` already present with graceful `PermissionError` fallback

---

## New Tests Added

| Test File | Count | Finding |
|-----------|-------|---------|
| `tests/execution_lane/test_paper_strategy_lifecycle.py` | 9 | M-01, M-02, L-03 |
| `tests/strategy_spec/test_output_mode_enforcement.py` | 3 | M-04 |
| `tests/auth/test_token_eviction.py` | 6 | C-01 |
| `tests/execution_lane/test_bounded_stores.py` | 7 | C-01 |
| `tests/evidence_ledger/test_evidence_startup_guard.py` | 5 | H-02 |
| `tests/execution_lane/test_multi_venue_config.py` | 5 | H-01 |
| **Total** | **35** | |

## Files Changed

| File | Change |
|------|--------|
| `packages/execution_lane/paper_strategy.py` | Added `bar_type`, `on_stop()`, `on_reset()`, `on_bar()` |
| `packages/strategy_spec/models.py` | Added `enforce_signal_preview_only` model validator |
| `packages/workflow_spine/postgres_repository.py` | Parameterized SQL LIMIT/OFFSET |
| `packages/auth/service.py` | Added TTL + LRU eviction + `revoke_token()` |
| `packages/execution_lane/service.py` | Added `max_reports`/`max_sessions` + eviction methods |
| `services/api/fastapi_app.py` | Added startup event evidence re-validation guard |

## Pre-existing Failures (not from this change)

- `tests/integration/test_catalog_replay_ledger_updates.py::test_catalog_backed_replay_master_reconciliation_is_recorded_in_ledgers`
- `tests/onboarding/test_open_findings.py::TestL9TokenExposureDocumentation::test_findings_documents_l9`
