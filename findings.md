# Deep Review Findings — nautilus_builder + Nautilus-Daedalus

**Review Date:** 2026-06-12
**Reviewer:** Autonomous code-reviewer + architect lanes
**Scope:** Both repos, full tree, NT v1.227.0/v1.228.0 API alignment
**Test Evidence:** Builder 1479 passed / 1 skipped; Daedalus ~3130 tests (partial UI failures)

---

## CODE REVIEW REPORT

Files Reviewed: 85+ (critical paths)
Total Issues: 24
Architectural Status: WATCH

---

### CRITICAL (2)

**C-01: NT version pin mismatch in Daedalus pyproject.toml**
- File: `Nautilus-Daedalus/pyproject.toml:3`
- Issue: `nautilus_trader==1.228.0` declared but installed version is `1.227.0`. This creates a silent version drift where tests pass against 1.227.0 but production would install 1.228.0 with potentially different APIs (especially `fill_limit_at_touch` → `fill_limit_inside_spread` rename in v1.224, or Quantity subtraction returning ValueError in v1.223+).
- Risk: Runtime failures in production when uv/pip resolves to 1.228.0. Any breaking change between 1.227 and 1.228 would surface only at deploy time.
- Fix: Either pin to `1.227.0` to match the tested version, or upgrade the environment and run the full test suite against 1.228.0.

**C-02: Unbounded in-memory credential/token stores in production path**
- Files: `packages/auth/service.py`, `packages/execution_lane/service.py`
- Issue: `AuthTokenService._tokens` is a plain `dict[str, UserProjectContext]` with no eviction, TTL, or size limit. `ExecutionLaneService._sessions`, `_profiles`, `_commands`, `_reports` are all unbounded dicts. In a long-running production FastAPI process, these grow without bound.
- Risk: Memory exhaustion under sustained load. Tokens issued for testing (`nb_test_*`) are never cleaned up.
- Fix: Add TTL-based eviction or LRU cap for auth tokens. Consider Postgres-backed session persistence for execution lane state in production (the `postgres_repository.py` exists but the in-memory service is the default).

---

### HIGH (5)

**H-01: Adapter config builder only supports Binance**
- File: `packages/execution_lane/adapter_config_builders.py`
- Issue: Only `build_binance_data_config()` and `build_binance_exec_config()` exist. The `build_generic_data_config()` function exists but raises `ValueError` for non-Binance venues. Daedalus has adapters for Extended, Ethereal, O1XYZ, StandX, Apex Omni — none are wired.
- Risk: Execution lane paper sessions fail for any non-Binance venue. This blocks multi-venue strategy testing.
- Fix: Add adapter config builders for all venues used in Daedalus, or make `build_generic_data_config()` fall back to a safe default config pattern.

**H-02: Custom message bus bypasses NT publish_signal/publish_data**
- File: `Nautilus-Daedalus/nautilus_actors/nt_actor_bus.py`
- Issue: `subscribe_topic()` and `publish_topic()` use `bus.subscribe(topic, callback)` and `bus.publish(topic, payload)` directly, with JSON-encoded strings. This bypasses NautilusTrader's typed `publish_signal()` and `publish_data()` APIs which are the canonical patterns for Actor-to-Strategy communication per NT architecture docs.
- Risk: Loss of NT message bus guarantees (typed routing, DataType matching, backpressure). Custom bus has no type safety — any string payload passes.
- Fix: Migrate to `self.publish_signal()` for primitives and `self.publish_data(DataType(...), data)` for structured data. Keep the topic bus as a compatibility shim during transition.

**H-03: TradeDecisionActor uses asyncio.gather inside NT Actor**
- File: `Nautilus-Daedalus/nautilus_actors/trade_decision_actor.py`
- Issue: Uses `asyncio.gather(*tasks, return_exceptions=True)` for concurrent postmortem learning. NT runs on a single thread with an event-driven model; spawning concurrent coroutines inside Actor handlers can cause re-entrancy issues if the gathered tasks access shared actor state.
- Risk: Race conditions on `_tasks` dict, potential double-processing of signals.
- Fix: Serialize postmortem processing or use an off-actor background worker with proper synchronization.

**H-04: ExtendedExecutionClient missing reconciliation methods**
- File: `Nautilus-Daedalus/nautilus_adapters/adapters/extended/execution.py`
- Issue: Uses `unsupported_reconciliation` from a local helper. The NT adapter contract requires reconciliation for production execution clients. The client generates fill reports but delegates mass-status and position-status to unsupported stubs.
- Risk: In live trading, position reconciliation on startup is not possible. State drift between NT cache and venue could lead to duplicate or missed orders.
- Fix: Implement `generate_execution_mass_status()` and `generate_position_status()` using venue REST endpoints, or explicitly document that this adapter is paper/testnet only.

**H-05: Evidence production fail-closed only enforced at app factory level**
- File: `services/api/fastapi_app.py`
- Issue: The ValueError for in-memory evidence in production is raised inside `create_fastapi_app()`, which is only called during server startup. If a developer bypasses the factory and creates a FastAPI app directly (e.g., in tests or scripts), the guard is skipped.
- Risk: Misconfigured production deployment without evidence persistence.
- Fix: Add a startup event handler that re-validates evidence storage config, or make the check a FastAPI dependency.

---

### MEDIUM (9)

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

**M-04: EvoMapCapsuleAdvisoryActor uses `time.monotonic()` instead of NT clock**
- File: `Nautilus-Daedalus/nautilus_actors/evomap_capsule_advisory_actor.py`
- Issue: Capsule TTL check uses `time.monotonic()` rather than `self.clock`. This breaks determinism in backtests and DST environments.
- Fix: Use `self.clock.timestamp_ns()` or `self.clock.elapsed()` for TTL checks.

**M-05: Daedalus test failures in Telegram Signal UI suite**
- Files: `tests/test_telegram_signal_*.py` (14+ failures observed)
- Issue: Telegram signal CLI, process, schema, and UI dialog tests are failing. These appear to be contract tests that encode assumptions about legacy operator imports and stream defaults that may have changed.
- Risk: Signal delivery pipeline may be broken or tests encode stale contracts.
- Fix: Investigate and fix the 14+ failing tests. If they test deprecated behavior, update the tests; if they test current behavior, fix the implementation.

**M-06: `_bayesian_confidence_shadow` fallback produces misleading data**
- File: `Nautilus-Daedalus/nautilus_actors/trade_decision_actor.py:286+`
- Issue: When Bayesian confidence is missing, the function returns a synthetic shadow with `confidence_quality: "insufficient"` but still populates numeric fields with zeros. Downstream consumers may not check `confidence_quality` and treat zeros as valid metrics.
- Fix: Return `None` or raise when confidence is missing, forcing explicit handling.

**M-07: StrategySpec classic model doesn't enforce `output_mode=signal_preview_only`**
- File: `packages/strategy_spec/models.py`
- Issue: The v1 `StrategySpec` has `OutputMode.SIGNAL_PREVIEW_ONLY` as the only enum value, but doesn't have a model validator enforcing it (unlike `StrategySpecMicrostructureV1` which has an explicit `Literal[False]` guard on `execution_authority`).
- Risk: If new output modes are added to the enum without updating validators, the classic spec could accept them silently.
- Fix: Add a model validator that enforces `output_mode == SIGNAL_PREVIEW_ONLY`.

**M-08: Version consistency test may not catch Daedalus drift**
- File: `tests/version/test_version_consistency.py`
- Issue: Builder has version consistency tests, but Daedalus `pyproject.toml` pins `1.228.0` while installed is `1.227.0`. There's no cross-repo version alignment check.
- Fix: Add a CI check that verifies Daedalus pyproject.toml NT version matches the actually installed/tested version.

**M-09: No structured logging/observability in Daedalus actors**
- Files: `nautilus_actors/trade_decision_actor.py`, `nautilus_actors/gate_actor.py`
- Issue: Actors use `self._logger.error(message)` with formatted strings instead of structured logging. Error events are formatted as space-delimited key=value strings rather than JSON.
- Risk: Difficult to parse, aggregate, or alert on actor errors in production monitoring.
- Fix: Use Python `structlog` or NT's built-in logging with structured fields.

---

### LOW (8)

**L-01: `_installed_nautilus_version()` always returns None**
- File: `packages/execution_lane/nautilus_runtime.py:183`
- Issue: The function has a `try: import nautilus_trader; return None` — the `return None` is inside the try block before any version extraction. Dead code.
- Fix: Change to `return str(getattr(nautilus_trader, "__version__", "")) or None`.

**L-02: Starlette deprecation warning in test client**
- Issue: `StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated; install httpx2 instead`.
- Fix: Update FastAPI/Starlette dependency or install `httpx2`.

**L-03: No type hints on several Daedalus adapter methods**
- Files: `nautilus_adapters/adapters/extended/execution.py`, `nautilus_adapters/adapters/extended/client.py`
- Issue: Several methods use `object | None` for parameters that should be typed.
- Fix: Add proper type annotations.

**L-04: `coerce_config_arg` docstring mentions "temporary message-bus override"**
- File: `Nautilus-Daedalus/nautilus_actors/nt_actor_bus.py`
- Issue: The compatibility layer for dual-constructor actors is necessary but the docstring could be clearer about the NT ActorFactory contract.
- Fix: Add a reference to the NT ActorFactory docs.

**L-05: Evidence repository field mapping tests cover Postgres but not migration rollback**
- File: `packages/evidence_ledger/postgres_repository.py`
- Issue: Migration v7 creates `evidence_refs` table, but there's no rollback path tested.
- Fix: Add a downgrade migration test.

**L-06: Missing `on_stop` in `ExecutionLanePaperStrategy`**
- File: `packages/execution_lane/paper_strategy.py`
- Issue: No explicit unsubscribe in `on_stop()`. NT framework handles cleanup, but explicit unsubscribe is recommended per NT conventions.
- Fix: Add `on_stop()` with `self.unsubscribe_quote_ticks()`.

**L-07: `reveal_secret()` in Daedalus credential resolution doesn't audit access**
- File: `Nautilus-Daedalus/nautilus_adapters/adapters/credential_resolution.py`
- Issue: Secret values are resolved without logging access. For audit compliance, credential access should be logged (without the value).
- Fix: Add an optional audit logger that records which credential was accessed.

**L-08: No `.env.execution.local` file permission validation**
- File: `packages/execution_lane/credentials.py`
- Issue: The credential slot store writes to `.env.execution.local` but doesn't validate that the file has restrictive permissions (0600). `_validate_env_file_path` checks for path separators but not file mode.
- Fix: Add `os.chmod(path, 0o600)` after writing, or validate existing permissions.

---

## ARCHITECTURE WATCHLIST

**AW-01: Dual-repo architecture creates synchronization risk**
- Concern: Builder and Daedalus share NT contract types (TradeAction, StrategySpec) but live in separate repos with independent dependency pins. A breaking change in one repo's contract models can silently break the other.
- Status: WATCH
- Recommendation: Consider a shared contract package (`nautilus_contracts`) published as a library, or add cross-repo contract compatibility tests in CI.

**AW-02: Custom message bus topic system may not scale to LiveNode**
- Concern: Daedalus uses string-based topic pub/sub via `nt_actor_bus.py`. If the system migrates to Rust LiveNode, this custom bus won't transfer. NT's native `publish_signal`/`publish_data` would.
- Status: WATCH
- Recommendation: Create a migration plan from topic-based bus to NT-native typed signals.

**AW-03: Execution lane in-memory defaults may not survive production restarts**
- Concern: All execution lane state (profiles, commands, sessions, reports) lives in memory by default. A process restart loses all in-flight session state.
- Status: WATCH
- Recommendation: Ensure production deployments use the Postgres-backed repositories from the start, not just for evidence.

**AW-04: EvoMap advisory is correctly non-blocking but audit trail is file-based**
- Concern: `evomap_orchestrator.py` persists state to a local JSON file (`state_path`). In a distributed deployment, this won't be shared across instances.
- Status: WATCH
- Recommendation: Migrate EvoMap state to Postgres/Redis for multi-instance deployments.

---

## LEGACY/DEPRECATION CLOSURE INVENTORY

| Item | Status | Location | Action |
|------|--------|----------|--------|
| `credential_slot_http_disabled` response | ✅ Closed | `credentials.py:47` | Already returns 410 |
| Browser credential bootstrap | ✅ Closed | `credentials.py:46-48` | Returns error payload |
| `CredentialSlotBootstrap.tsx` | ✅ Closed | handguard guard | Asserted absent |
| `strategy_lane_coupled` | ✅ Hardcoded False | `models.py:150`, `nautilus_runtime.py:36` | Literal[False] enforced |
| `browser_credentials_allowed` | ✅ Hardcoded False | `config_contract.py:10,20` | Literal[False] enforced |
| `credential_inputs_allowed` | ✅ Hardcoded False | `service.py` snapshot | Always False |
| Coinbase International adapter (NT v1.224 removal) | ✅ Not referenced | N/A | No action needed |
| dYdX v3 adapter (NT v1.223 removal) | ✅ Not referenced | N/A | No action needed |
| `fill_limit_at_touch` (NT v1.224 rename) | ✅ Not used | N/A | No action needed |
| `TradeAction` retired keys rejection | ✅ Active | `trade_action.py:97` | Validator rejects retired keys |
| Legacy operator imports in Telegram CLI | ⚠️ Tests failing | `test_telegram_signal_cli.py` | 14 tests need reconciliation |
| `_installed_nautilus_version()` dead code | 🔧 Bug | `nautilus_runtime.py:183` | Returns None always |
| `may_submit_order` / `execution_authority` | ✅ Hardcoded False for paper | `models.py:62-63,194-195` | Paper blocks both |

---

## SYNTHESIS

- code-reviewer recommendation: **REQUEST CHANGES** (2 CRITICAL, 5 HIGH)
- architect status: **WATCH** (4 architectural concerns, no blockers)
- final recommendation: **REQUEST CHANGES**

Address CRITICAL items (version pin mismatch, unbounded stores) and at minimum H-01 (multi-venue adapter support) and H-04 (reconciliation) before considering production deployment.
