# Nautilus Builder — Deep Code Review Findings (2026-06-12)

## Review Scope

- **Repo**: `/home/mok/projects/nautilus_builder`
- **Reference**: `/home/mok/projects/Nautilus-Daedalus`
- **Packages reviewed**: 36 domain packages (~12,800 LOC)
- **Test baseline**: 1,441 passed, 1 integration failure, 1 skipped
- **Review dimensions**: Alignment, Bugs, Security, Maintainability, Architecture, Legacy/Deprecation
- **Authoritative refs**: NautilusTrader v1.227.0, nt-review/nt-architect/nt-live/nt-adapters/nt-testing skills

---

## Executive Summary

The codebase is well-structured with strong security posture and correct NautilusTrader API usage for the Python live/integration-specific TradingNode surface. Production fail-closed config is exemplary. The main risk areas are: one integration test failure blocking CI, a broad `except Exception` in pipeline compilation, rate limiting that fails open when Redis is down, and the execution_lane package being a single ~1900 LOC module that should be decomposed per Daedalus precedent.

**Architectural Status: WATCH**
**code-reviewer Recommendation: COMMENT**

---

## CRITICAL (0)

None.

---

## HIGH (4)

### H-01: Integration test failure blocks full CI pass
- **File**: `tests/integration/test_catalog_replay_ledger_updates.py`
- **Issue**: `test_catalog_backed_replay_master_reconciliation_is_recorded_in_ledgers` asserts that `structure.md` contains "Master reconciliation — catalog-backed Nautilus replay", but the file was overwritten during prior review cycles without preserving that entry.
- **Risk**: CI cannot report green; any future change may be masked by pre-existing failure.
- **Fix**: Either add the expected reconciliation entry to `structure.md` or update the test assertion to match the current documentation contract. Prefer documenting the catalog replay capability under a "Backtest Runner" section.
- **Category**: Bug / Alignment

### H-02: Pipeline compilation swallows all exceptions silently
- **File**: `packages/pipeline/service.py:68`
- **Issue**: `except Exception:` catches and discards all compilation errors, recording only a generic "failed" status without preserving the root cause message.
- **Risk**: Strategy compilation failures become opaque; operators cannot diagnose why a spec fails to compile from the pipeline step output alone.
- **Fix**: Capture the exception message in the failed step metadata:
  ```python
  except Exception as exc:
      steps.append(PipelineStep(name="compile", status="failed", detail=str(exc)))
  ```
- **Category**: Maintainability

### H-03: Redis rate limiter fails open — no production circuit breaker
- **File**: `packages/auth/redis_rate_limit.py:44,71`
- **Issue**: When Redis is unavailable, rate limiting falls back to allowing all requests with a warning log. This is acceptable for development but dangerous in production.
- **Risk**: An attacker can trivially DDoS the API by taking Redis offline (or causing connection failures). All rate limits vanish simultaneously.
- **Fix**: Add a production-mode toggle that fails closed (returns 503) when Redis is unreachable, or implement a local in-memory token bucket as degraded fallback with reduced limits.
- **Category**: Security

### H-04: Schema name string interpolation in SQL migrations
- **File**: `packages/postgres/migrations.py:87-119`
- **Issue**: Schema name is interpolated into SQL via `f"...{schema}..."` in `ensure_schema`, `current_version`, `apply_migrations`, and `rollback`. The schema is validated through `safe_postgres_identifier()` which constrains to `[A-Za-z_][A-Za-z0-9_]*`.
- **Risk**: Currently safe due to the identifier validation. However, this pattern is fragile — any future call site that bypasses `safe_postgres_identifier` introduces SQL injection. The migration SQL templates also use `{schema}` interpolation in `Migration.up`/`Migration.down` strings.
- **Fix**: This is an architectural WATCH rather than an immediate fix. Consider using `pggeo`-style identifier quoting (`"identifier"`) or prepared statements for schema operations. Document that all call sites MUST pass through `safe_postgres_identifier`.
- **Category**: Security (defense in depth)

---

## MEDIUM (10)

### M-01: `ExecutionLaneSession.status` duplicated as `lifecycle_status`
- **File**: `packages/execution_lane/sessions.py` (ExecutionLaneSession model)
- **Issue**: The model has both `status` and `lifecycle_status` fields with identical `Literal` types (`"INITIALIZED" | "RUNNING" | "STOPPED" | "DISPOSED" | "FAILED"`). No code appears to diverge them.
- **Risk**: Fields can drift — one updated while the other is not — leading to inconsistent state reporting.
- **Fix**: Remove one or document the semantic distinction. If `status` is the API-facing field and `lifecycle_status` tracks Nautilus component state, add a comment clarifying the difference and ensure they are always updated together.
- **Category**: Alignment / Maintainability

### M-02: Paper strategy has no logging
- **File**: `packages/execution_lane/paper_strategy.py`
- **Issue**: The `ExecutionLanePaperStrategy` never calls `self.log.info()` or `self.log.debug()` in any lifecycle method. NT best practice is to log state transitions in `on_start`, `on_stop`, and `on_reset`.
- **Risk**: Operators have zero visibility into paper strategy lifecycle when debugging execution lane sessions.
- **Fix**: Add logging to `on_start` (instrument found/not found, subscription type), `on_stop`, `on_bar`/`on_quote_tick` (at debug level with counts), and `on_reset`.
- **Category**: Maintainability / NT Conventions

### M-03: `urllib.request.urlopen` for LLM transport without SSL verification control
- **File**: `packages/ai_builder/provider.py:265`
- **Issue**: `_urllib_json_transport` uses `urllib.request.urlopen` with `# noqa: S310` suppressing the bandit warning. No explicit SSL context or certificate verification configuration.
- **Risk**: In environments with custom CA bundles or MITM proxies, this may silently fail or connect to unintended endpoints.
- **Fix**: Either use `httpx` with explicit SSL configuration, or create an `ssl.SSLContext` with explicit cert verification and pass it to `urlopen`. Remove the `noqa` once resolved.
- **Category**: Security

### M-04: Thread-based TradingNode runner lacks graceful shutdown
- **File**: `packages/execution_lane/sessions.py:186-190`
- **Issue**: `NativeTradingNodeSessionRunner.start()` spawns a daemon thread with `node.run()`. The `stop()` method calls `node.stop()` but has no timeout or join mechanism. If `node.stop()` hangs (e.g., adapter disconnect timeout), the thread runs indefinitely.
- **Risk**: Orphaned TradingNode threads can accumulate if sessions fail to shut down cleanly, leaking resources and potentially keeping exchange connections alive.
- **Fix**: Add a `thread.join(timeout=30)` after `node.stop()` with a warning log if the join times out. Consider a `threading.Event` for cooperative cancellation.
- **Category**: Bug / Maintainability

### M-05: Credential slot resolution logs warning but continues
- **File**: `packages/execution_lane/sessions.py` (around line 380+)
- **Issue**: When credential resolution fails, the code catches `ValueError`, logs a warning, and continues. This may lead to sessions starting without valid credentials.
- **Risk**: Session starts with empty credential values, leading to confusing adapter errors downstream rather than clear upfront validation failures.
- **Fix**: Re-raise the `ValueError` after logging, or return an explicit failure status rather than proceeding.
- **Category**: Bug

### M-06: `on_bar`/`on_quote_tick` counters are unbounded in long sessions
- **File**: `packages/execution_lane/paper_strategy.py:57-59`
- **Issue**: `observed_quote_ticks` and `observed_bars` are simple incrementing counters with no upper bound. In multi-day paper sessions, these grow indefinitely.
- **Risk**: Minimal practical risk (counters are just integers), but inconsistent with NT pattern of bounded state.
- **Fix**: No immediate action needed, but document that these are session-scoped counters reset by `on_reset`.
- **Category**: Maintainability

### M-07: `_installed_nautilus_version()` catches all exceptions broadly
- **File**: `packages/execution_lane/nautilus_runtime.py:283-286`
- **Issue**: `except Exception: return None` catches `ImportError` (expected) but also masks `AttributeError`, `TypeError`, etc. if nautilus_trader is installed but corrupted.
- **Risk**: Silent `None` return may cause downstream code to skip version validation.
- **Fix**: Catch only `ImportError` for the import, and let other exceptions propagate.
- **Category**: Maintainability

### M-08: Evidence ledger startup guard only fires at app factory level
- **File**: `packages/evidence_ledger/` + `services/api/fastapi_app.py`
- **Issue**: The evidence startup guard prevents production startup with InMemory evidence repository. However, if someone constructs an `EvidenceLedgerService` directly (e.g., in a worker or CLI), the guard is bypassed.
- **Risk**: A misconfigured worker process could use in-memory evidence in production without the startup guard catching it.
- **Fix**: Add a secondary guard in `EvidenceLedgerService.__init__` or its factory that checks for production environment and rejects in-memory repositories.
- **Category**: Security / Maintainability

### M-09: `on_start` subscribes without `request_bars` warmup
- **File**: `packages/execution_lane/paper_strategy.py:43-47`
- **Issue**: Per nt-review best practices, `request_bars()` should be called before `subscribe_bars()` to warm up indicators with historical data. The paper strategy jumps directly to subscription.
- **Risk**: Low for an observational strategy (no trading logic), but inconsistent with NT conventions. If the strategy ever gains indicators, it will have a cold start.
- **Fix**: Add `self.request_bars(bar_type=self.config.bar_type)` before the subscribe call, or document that this is intentional for an observational-only strategy.
- **Category**: NT Alignment

### M-10: No test coverage for `NativeTradingNodeSessionRunner.stop()` edge cases
- **File**: `packages/execution_lane/sessions.py`
- **Issue**: The runner's `stop()` method pops from `_sessions` dict without checking if the session exists. A double-stop or stop-without-start raises `KeyError`.
- **Risk**: Production crash if stop is called twice (e.g., timeout + manual stop).
- **Fix**: Use `self._sessions.pop(session_id, None)` and log a warning if not found, or raise a typed `ExecutionLaneError`.
- **Category**: Bug

---

## LOW (6)

### L-01: `_DEMO_TOKENS` set in production config includes "my-secret-prod-key-2026"
- **File**: `packages/config/production.py:18`
- **Issue**: The demo token list contains a string that looks like a real production key pattern. While this is correctly rejected in production, the string itself could cause confusion.
- **Fix**: Rename to something clearly synthetic like `EXAMPLE-DO-NOT-USE-prod-key-2026`.
- **Category**: Maintainability

### L-02: `Future_runtime` field is a placeholder
- **File**: `packages/execution_lane/nautilus_runtime.py` (NautilusTradingNodeRuntimePlan)
- **Issue**: `future_runtime: Literal["rust_live_node"]` is always `"rust_live_node"` — a static placeholder with no implementation.
- **Fix**: Document that this is a forward-compatibility field, or remove until Rust LiveNode integration is planned.
- **Category**: Alignment

### L-03: `strategy_lineage_id` appears in both session and paper strategy config
- **File**: `packages/execution_lane/sessions.py` + `paper_strategy.py`
- **Issue**: The lineage ID is passed through multiple layers (session → runtime plan → strategy config) without a clear provenance chain.
- **Fix**: Add a comment documenting the flow: spec → command → session → runtime plan → paper strategy config.
- **Category**: Maintainability

### L-04: No type hints on `NativeTradingNodeSessionRunner._sessions` inner types
- **File**: `packages/execution_lane/sessions.py:152`
- **Issue**: `dict[str, tuple[Any, threading.Thread]]` — the `Any` obscures that the first element is a `TradingNode` instance.
- **Fix**: Use `tuple[TradingNode, threading.Thread]` or a `NamedTuple`.
- **Category**: Maintainability

### L-05: `urllib` used instead of `httpx` for LLM calls
- **File**: `packages/ai_builder/provider.py`
- **Issue**: The project has `httpx` as an optional dependency but uses `urllib.request` for OpenAI API calls. `httpx` provides async support, retries, and better timeout handling.
- **Fix**: Migrate to `httpx` for consistency with the rest of the stack (used in adapter patterns).
- **Category**: Maintainability

### L-06: No `py.typed` marker in packages directory
- **Issue**: The `packages/` directory is a namespace package without a `py.typed` marker, which means type checkers won't recognize it as typed.
- **Fix**: Add an empty `py.typed` file to `packages/` if the project intends to support PEP 561.
- **Category**: Maintainability

---

## ARCHITECTURE WATCHLIST

### A-01: Execution lane package is ~1900 LOC in a single module
- **Status**: WATCH
- **Concern**: Nautilus-Daedalus has already decomposed its execution lane into sub-modules under a 250 LOC ceiling. The builder's `execution_lane/` at ~1900 LOC is a single-layer package. This makes review harder and increases merge conflict risk.
- **Recommendation**: Plan a module split similar to Daedalus: `execution_node.py` → `execution_node_profile.py`, `execution_node_runner.py`, etc. Add a LOC boundary test like Daedalus's `test_execution_lane_module_boundaries.py`.

### A-02: Thread-per-session model for TradingNode runners
- **Status**: WATCH
- **Concern**: Each paper/live session spawns a new daemon thread with its own TradingNode. This doesn't scale to many concurrent sessions and makes graceful shutdown complex.
- **Recommendation**: Consider a session pool model or process-based isolation for production multi-session scenarios.

### A-03: No async boundary between FastAPI and TradingNode
- **Status**: WATCH
- **Concern**: FastAPI runs async, but TradingNode.run() is blocking. The bridge is a thread. If session management grows, consider process isolation or dedicated worker processes.
- **Recommendation**: Document the current thread bridge as intentional and note the planned evolution path.

### A-04: Evidence ledger is dual-backend (InMemory + Postgres) with runtime selection
- **Status**: WATCH
- **Concern**: The startup guard prevents InMemory in production, but the dual-backend pattern adds complexity. If Postgres is down at startup, the app fails to start rather than degrading.
- **Recommendation**: This is correct fail-closed behavior. Document this as a design decision.

### A-05: Rust LiveNode integration path is placeholder-only
- **Status**: WATCH
- **Concern**: `future_runtime="rust_live_node"` indicates planned Rust LiveNode support, but there is no implementation or migration plan.
- **Recommendation**: Create a design doc for the Rust LiveNode migration path before beginning implementation.

---

### L9: NEXT_PUBLIC_BUILDER_API_TOKEN client-side exposure
- **Status**: Documented in production config guard #8
- **File**: `packages/config/production.py`
- **Issue**: `NEXT_PUBLIC_BUILDER_API_TOKEN` is a Next.js client-side env variable. If set in production, it leaks the API token into the browser bundle.
- **Mitigation**: `BuilderProductionConfig._validate_production` raises `ValueError` if `has_browser_api_token=True`, preventing production startup.
- **Category**: Security (defense in depth)

## LEGACY / DEPRECATION CLOSURE REVIEW

### Completed Closures (verified)
| Item | Status | Evidence |
|------|--------|----------|
| PostgresWorkflowRepository → SqliteWorkflowRepository | ✅ Closed | `workflow_spine/__init__.py:37` has comment noting deprecation |
| Demo tokens rejected in production | ✅ Active | `_DEMO_TOKENS` set + `BuilderProductionConfig._validate_production` |
| Browser credential bootstrap disabled | ✅ Active | `credentials.py:47` returns error payload |
| Browser secret echo disabled | ✅ Active | `browser_secret_echo: Literal[False] = False` |
| Evidence fail-closed at factory | ✅ Active | `test_evidence_startup_guard.py` |
| Docker image no local env files | ✅ Active | `test_dockerfile_safety.py` |

### Pending Closures
| Item | Status | Risk | Recommendation |
|------|--------|------|----------------|
| `on_event` deprecation in FastAPI | ⚠️ Active | FastAPI deprecation warnings in test output (5 tests) | Migrate from `@app.on_event` to lifespan handlers |
| `urllib` transport for LLM | ⚠️ Active | No async, no retry, no connection pooling | Migrate to `httpx` with async support |
| Thread-per-session runner | ⚠️ Active | Doesn't scale, no graceful timeout | Plan worker-process model |

### No Legacy Debt Found
- No `@deprecated` decorators without migration path
- No dead imports or unused legacy modules detected
- No stale TODO/FIXME markers with legacy implications

---

## DAEDALUS ALIGNMENT GAPS

| Gap | Daedalus Pattern | Builder Current | Priority |
|-----|-----------------|-----------------|----------|
| Module LOC ceiling | <250 LOC per module with boundary tests | execution_lane ~1905 LOC single package | Medium |
| Rust paper execution | RustPaperExecutionAuthority | Python-only paper strategy | Low (placeholder exists) |
| Promotion evidence actors | Dedicated evidence/promotion actors | Service-layer promotion gate | Design-only |
| Session thread pool | Process-isolated sessions | Thread-per-session | Medium |

---

## SYNTHESIS

- **code-reviewer recommendation**: COMMENT (4 HIGH, 10 MEDIUM, 6 LOW — no CRITICAL security vulnerabilities)
- **architect status**: WATCH (execution lane module size, thread-per-session model, Rust LiveNode migration path)
- **final recommendation**: COMMENT

**Action items before next release**:
1. Fix H-01 (integration test failure)
2. Address H-02 (pipeline exception swallowing)
3. Evaluate H-03 (Redis fail-open rate limiter) for production deployment
4. Plan A-01 (execution lane module decomposition)

**Pre-existing issues noted but not modified**:
- FastAPI `on_event` deprecation warnings (LOW priority, not blocking)
- No `request_bars` warmup in paper strategy (intentional for observational-only)

---

## Master reconciliation — catalog-backed Nautilus replay

The `catalog_backed_replay_smoke` module validates NautilusTrader replay using synthetic historical quote ticks from the catalog_datasets layer. This is an evidence-gate smoke test, not full trading-production readiness.
