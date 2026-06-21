# Nautilus Builder — Deep Code Review Findings (2026-06-13)

## Review Scope

- **Repo**: `/home/mok/projects/nautilus_builder`
- **Reference**: `/home/mok/projects/Nautilus-Daedalus`
- **Packages reviewed**: 36 domain packages (~12,800 LOC)
- **Test baseline**: 1,441 passed, 1 integration failure, 1 skipped
- **Review dimensions**: Alignment, Bugs, Security, Maintainability, Architecture, Legacy/Deprecation
- **Authoritative refs**: NautilusTrader latest v1.228.0; local pin remains nautilus_trader==1.227.0; nt-review/nt-architect/nt-live/nt-adapters/nt-testing skills

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

## 2026-06-12 Deep Review Refresh — NT/AI Alignment and Legacy Closure

### Review scope and authority
- **Repo reviewed**: `/home/mok/projects/nautilus_builder` on `master`.
- **Reference repo checked**: `/home/mok/projects/Nautilus-Daedalus` at `e12b89d4` for Daedalus runtime alignment only.
- **Official source refresh (2026-06-12)**:
  - NautilusTrader latest release: `v1.228.0` / `NautilusTrader 1.228.0 Beta` (published 2026-06-08) from `https://github.com/nautechsystems/nautilus_trader/releases/latest`.
  - Local Builder pin remains `nautilus_trader==1.227.0` in `pyproject.toml:12` and `uv.lock`.
  - EvoMap/evolver latest checked: `v1.89.5` (2026-06-12) from `https://github.com/EvoMap/evolver/releases/latest`.
  - LangChain latest checked: `langchain-core==1.4.6` (2026-06-11) from `https://github.com/langchain-ai/langchain/releases/latest`.
  - LangGraph latest checked: `langgraph-cli==0.4.29` (2026-06-11) from `https://github.com/langchain-ai/langgraph/releases/latest`.
- **Independent review lane status**: Historical 2026-06-12 note: lanes were unavailable in that session. **Superseded 2026-06-13**: both `code-reviewer` and `architect` lanes completed and returned REQUEST CHANGES / BLOCK production-readiness claims.

### Executive synthesis
- **Final recommendation**: `COMMENT / NOT MERGE-READY AS APPROVAL` for production-readiness claims, because active high/medium risks remain; superseded by the 2026-06-13 independent-lane pass where lanes completed successfully.
- **Critical security findings**: none found in this pass.
- **Primary active risks**: Redis fail-open behavior under runtime Redis errors, pipeline compile error suppression, version/deprecation drift, FastAPI `on_event` deprecation, and incomplete DataTester/ExecTester evidence for any future adapter-readiness claim.
- **Positive alignment**: production startup policy remains fail-closed for missing API token/CORS/rate-limit backend; browser credential collection remains disabled; execution lane models enforce manual review/reconciliation fields for live authority; AI draft prompts reject credential requests and browser LLM config rejects secret-bearing fields.

### HIGH

#### H-20260612-01: Redis rate limiter can still fail open at runtime
- **Evidence**: `packages/auth/redis_rate_limit.py:44` catches Redis connection failures and falls back; `packages/auth/redis_rate_limit.py:71` catches runtime Redis command failures and logs `rate_limit_fallback_open` unless `fail_closed=True` is configured.
- **Risk**: production startup requires `BUILDER_RATE_LIMIT_BACKEND=redis`, but runtime Redis outages can still remove the effective API throttle if fail-closed is not wired through every production construction path.
- **Fix**: make production construction pass `fail_closed=True` unconditionally, add a test that simulates Redis command failure in production and expects denial/503, and document local-only fail-open behavior.

#### H-20260612-02: Pipeline compilation still suppresses root-cause exceptions
- **Evidence**: `packages/pipeline/service.py:66` wraps `compile_strategy_spec`, and `packages/pipeline/service.py:68` catches bare `Exception` while only emitting `PipelineStep(name="compile", status="failed")`.
- **Risk**: compile failures lose structured error details, making operator/audit triage hard and hiding whether the issue was validation, compiler, filesystem, or unexpected runtime failure.
- **Fix**: catch a typed compiler exception where possible; otherwise capture `type(exc).__name__` plus redacted message in `PipelineResult.error` or a new `PipelineStep.detail` field. Add a regression test asserting the compile failure reason survives.

#### H-20260612-03: Required independent review approval evidence was unavailable — SUPERSEDED
- **Evidence**: the requested `superpowers:code-review` workflow requires independent `code-reviewer` and `architect` lanes, and both native agent types were unavailable in that historical session; superseded by the 2026-06-13 pass where both lanes completed.
- **Risk**: review results can be committed as findings, but they must not be interpreted as an independent approval or merge-readiness sign-off.
- **Fix**: rerun the review in an environment where `code-reviewer` and `architect` lanes are available before promoting any production-readiness or deployment approval claim.

### MEDIUM

#### M-20260612-01: NautilusTrader version and docs are semantically stale
- **Evidence**: active dependency pin is `pyproject.toml:12` (`nautilus_trader==1.227.0`), while latest official release checked is `v1.228.0`; archived docs still reference `nautilus_trader==1.223.0` at `docs/superpowers/specs/2026-05-24-findings-closure-design.md:14`, `:52`, and `:98`.
- **Risk**: Builder review guidance and dependency policy can drift from current Nautilus API contracts (for example adapter/live/runtime/testing changes), causing false confidence in old guardrails.
- **Fix**: create a compatibility upgrade issue for `1.228.0`, run targeted Builder runtime/backtest tests against it, then either upgrade the pin or document why Builder intentionally stays on `1.227.0`. Move old `1.223.0` specs under an archive heading or mark them historical.

#### M-20260612-02: FastAPI startup hook uses deprecated `on_event`
- **Evidence**: `services/api/fastapi_app.py:203` checks `hasattr(app, "on_event")` and `services/api/fastapi_app.py:204` registers `@app.on_event("startup")`.
- **Risk**: current tests already record deprecation warnings; future FastAPI versions can remove or alter the API, weakening the evidence-storage startup guard.
- **Fix**: migrate startup revalidation into a lifespan context manager and keep a test proving production evidence storage still fails closed.

#### M-20260612-03: Native TradingNode session runner shutdown remains a lifecycle risk
- **Evidence**: `packages/execution_lane/sessions.py:152` stores active native node/thread tuples; `packages/execution_lane/sessions.py:166` starts native TradingNode sessions after an async-loop guard. Prior review also tracks missing robust stop/join coverage.
- **Risk**: without explicit join timeout/dispose assertions, a hung `node.stop()` or adapter disconnect can leave orphaned TradingNode threads and live venue connections.
- **Fix**: add stop-path tests around a fake node that hangs/fails, enforce bounded join timeout, and always transition the session record to a terminal state with clear operator evidence.

#### M-20260612-04: Adapter/live readiness claims must stay gated by DataTester/ExecTester evidence
- **Evidence**: repo currently has backtest/replay smoke evidence and Python live/integration-specific TradingNode scaffolding, but no DataTester/ExecTester matrix for venue adapter readiness.
- **Risk**: future docs or UI labels could overstate adapter conformance. Nautilus adapter/testing guidance requires DataTester-compatible evidence for data behavior and ExecTester-compatible evidence for execution lifecycle claims.
- **Fix**: keep current wording as scaffold/contract evidence only. Add DataTester/ExecTester artifact fields before any adapter is labelled production-ready.

#### M-20260612-05: Execution lane package remains large enough to slow review and ownership
- **Evidence**: `packages/execution_lane` is ~1905 LOC across 10 Python files; `sessions.py` is ~434 LOC and `models.py` is ~325 LOC.
- **Risk**: lifecycle, credentials, paper/live authority, and runtime-plan contracts are coupled enough that future changes may miss one guard or test seam.
- **Fix**: split `sessions.py` into runner protocol, sandbox runner, native runner, and session ID/result helpers once behavior is locked by tests.

### LOW

#### L-20260612-01: Historical docs contain legacy Nautilus pins and old status language
- **Evidence**: `docs/superpowers/plans/2026-05-24-findings-closure-implementation-plan.md` and related archived specs still reference `nautilus_trader==1.223.0`; `docs/superpowers/specs/2026-05-30-quantdinger-fluidity-gap-design.md:100` references `1.227.0` as current.
- **Risk**: low if treated as historical, but confusing for semantic search and future agents.
- **Fix**: add a one-line archive banner to `docs/superpowers/*` plans/specs that old version pins are historical snapshots, not current policy.

#### L-20260612-02: UI placeholders are intentional but should remain labelled as non-authoritative
- **Evidence**: README already says placeholder UI components do not replace backend runtime truth; web tests include placeholder chart labels.
- **Risk**: low; if copied into operator docs without labels, placeholders can be mistaken for real readiness signals.
- **Fix**: keep placeholder labels explicit and ensure `tests/web` continues to assert authority boundaries.

### Inventory-first semantic legacy/deprecation closure

| Inventory item | Status | Evidence | Closure action |
| --- | --- | --- | --- |
| `PostgresWorkflowRepository` naming drift | Closed | `findings.md` tracks `PostgresWorkflowRepository → SqliteWorkflowRepository` as closed; `docs/deprecations/deprecation-inventory.md` records removal. | Keep closed; do not reintroduce alias. |
| `allow_legacy_fixture_refs` | Closed | `tests/promotions/test_shadow_evidence_contract.py` notes legacy warning filter removed and strict legacy ref tests remain. | Keep closed; keep strict scoped artifact refs. |
| FastAPI `on_event` | Active | `services/api/fastapi_app.py:203`/`:204`. | Migrate to lifespan. |
| Nautilus 1.223 archived specs | Active semantic drift | `docs/superpowers/specs/2026-05-24-findings-closure-design.md:14`. | Mark historical or update current policy pointer. |
| Nautilus 1.227 runtime pin vs latest 1.228 | Active watch | `pyproject.toml:12`; GitHub latest `v1.228.0`. | Compatibility test before upgrade. |
| Rust LiveNode placeholder field | Active watch | `structure.md` records `future_runtime="rust_live_node"` placeholder. | Keep labelled as placeholder until real Rust LiveNode path exists. |
| Browser credential bootstrap | Active guard | `packages/execution_lane/credentials.py` returns disabled payload and validates env-only backend slot writes. | Keep active; no browser secret collection. |
| AI/EvoMap/LangChain advisory boundary | Active guard | AI builder rejects credential prompts; LLM config rejects secret fields. | Keep AI sidecar/advisory-only; never execution-authoritative. |

### Validation run during this review
- `python3 scripts/check_docs_consistency.py` -> passed.
- `python3 -m pytest tests/integration/test_operability_baseline.py tests/onboarding/test_env_and_scripts.py tests/promotions/test_shadow_evidence_contract.py -q` -> 37 passed.
- Broader tests are run after markdown updates before commit.

### Review gate outcome
- **code-reviewer lane**: unavailable.
- **architect lane**: unavailable.
- **Architectural status**: `WATCH` locally, because active production/runtime risks remain but no new CRITICAL blocker was found.
- **Final recommendation**: `COMMENT`; do not treat this as merge-ready approval until active high findings are resolved; independent lanes completed in the 2026-06-13 pass.

---

# 2026-06-13 Deep Code Review — Independent NT / Architecture Pass

## Review scope

- **Primary repo/ledger edited**: `/home/mok/projects/nautilus_builder`
- **Implementation reference inspected**: `/home/mok/projects/Nautilus-Daedalus`
- **Independent lanes completed**: `code-reviewer` (`REQUEST CHANGES`) and `architect` (`BLOCK` for production-readiness claims)
- **Local inventory**: semantic legacy/deprecation scan, security grep, adapter/runtime evidence grep, module-size inventory, readiness/test-contract checks.
- **External authority**: NautilusTrader official adapter guide, Data Testing Spec, Execution Testing Spec, and upstream Hyperliquid Rust adapter layout. EvoMap/LangChain/LangGraph are process-only references for auditable/durable advisory workflows.

## Executive verdict

**Recommendation: REQUEST CHANGES / NOT PRODUCTION-READY.** No CRITICAL vulnerability was found in this documentation/code review pass, but active HIGH findings remain. Production-readiness approval is blocked until fail-open safety gates, silent execution-path failures, SQL hardening, and adapter evidence gaps are closed with tests.

### Severity summary

| Severity | Count | Current disposition |
|---|---:|---|
| CRITICAL | 0 | None found in this pass |
| HIGH | 6 total / 5 active | H-20260613-01 closed by this ledger update; H-20260613-02 through H-20260613-06 remain active |
| MEDIUM | 14 | Existing 10 plus 4 new review findings |
| LOW | 9 | Existing 6 plus 3 new review findings |

## HIGH findings

### H-20260613-01: Catalog replay ledger phrase missing from all ledgers — CLOSED BY THIS DOC UPDATE

- **Evidence**: `tests/integration/test_catalog_replay_ledger_updates.py` asserts all three ledgers include `Master reconciliation — catalog-backed Nautilus replay`, and `handguard.md` includes `CATALOG_BACKED_REPLAY_SMOKE_MODE`.
- **Fix applied here**: This 2026-06-13 update adds `Master reconciliation — catalog-backed Nautilus replay` to `structure.md`, `findings.md`, and `handguard.md`, and preserves `CATALOG_BACKED_REPLAY_SMOKE_MODE` in `handguard.md`.
- **Risk**: CI/documentation contract failure if removed again.
- **Status**: Closed pending verification command.

### H-20260613-02: Pipeline compilation swallows all exceptions silently — ACTIVE

- **Repo/file**: Builder, `packages/pipeline/service.py:68-69`.
- **Issue**: `except Exception:` appends `PipelineStep(name="compile", status="failed")` without exception type or redacted message.
- **Risk**: Root-cause evidence is lost; security- or correctness-relevant failures can be hidden.
- **Fix**: Record `type(exc).__name__` and a redacted message in `PipelineStep.detail`; add regression coverage.

### H-20260613-03: Redis rate limiter fails open in production — ACTIVE

- **Repo/file**: Builder, `packages/auth/redis_rate_limit.py:1-5,44-73`.
- **Issue**: The class explicitly documents fail-open behavior and allows requests when Redis errors unless constructed otherwise.
- **Risk**: Production API throttling disappears during Redis outage.
- **Fix**: Force `fail_closed=True` for production construction and add a production-mode Redis-failure test expecting denial/503.

### H-20260613-04: Schema identifier interpolation remains fragile — ACTIVE

- **Repo/file**: Builder, `packages/postgres/migrations.py:84-119`.
- **Issue**: Schema names are validated by `safe_postgres_identifier()` but then interpolated into SQL f-strings.
- **Risk**: Any future bypass of validation can become SQL injection; the pattern invites unsafe copy/paste.
- **Fix**: Centralize identifier quoting/formatting and test all callers; keep the safe identifier guard mandatory.

### H-20260613-05: Missing runtime health defaults to healthy in live graph runner — ACTIVE

- **Repo/file**: Daedalus, `nautilus_runtime/live/graph_runner.py:436,456`.
- **Issue**: `_coerce_runtime_bool(..., default=True)` treats missing `api_connected` and `data_quality_ok` as healthy.
- **Risk**: Kill-switch / data-quality decisions can proceed when monitoring data is absent or malformed.
- **Fix**: Default missing safety telemetry to `False`/unknown and add tests for absent micro-health payloads.

### H-20260613-06: Execution adapters swallow order-processing exceptions — ACTIVE

- **Repo/files**: Daedalus, `nautilus_adapters/adapters/apex_omni/execution.py`, `edgex/execution.py`, `ethereal/execution.py`, `extended/execution.py`.
- **Evidence**: Broad `except Exception` / `pass` around submit/modify/cancel paths at e.g. `apex_omni:318,360,366`, `edgex:318,360,366`, `ethereal:260,302,308`, `extended:240,282,288`.
- **Risk**: Failed order submission/cancel/modify can disappear without NT engine propagation or operator visibility.
- **Fix**: Use typed adapter errors, structured error logging, and generate rejection/failure events where Nautilus expects them.

## MEDIUM findings

| ID | Area | Evidence | Action |
|---|---|---|---|
| M-20260613-01 | Builder/Daedalus NT version drift | Builder pins `nautilus_trader==1.227.0`; Daedalus pins `1.228.0` | Align or document divergence with a migration deadline |
| M-20260613-02 | Daedalus adapter test coverage | Adapter readiness specs exist, but venue coverage is replay-heavy and lacks full DataTester/ExecTester artifacts | Establish minimum adapter evidence per venue/capability |
| M-20260613-03 | Adapter WebSocket clients use `print()` | `apex_omni`, `pacifica`, `edgex` clients print connection/parse events | Replace with structured NT logger usage |
| M-20260613-04 | Production composition root ambiguity | `run_full_stack` is manifest/dry-run/local-only, not supervisor | Keep docs explicit; add a separate supervisor only if needed |
| M-20260613-05 | AI/Telegram storage-chain coupling | AI and Telegram read PostgreSQL archive projections | Version schemas; keep one-way no-write-back DAG |
| M-20260613-06 | Dual execution-report paths | `execution_lane_process.py` and `execution_lane_bridge.py` are adjacent report paths | Pin canonical production path and label support/test path |
| M-20260613-07 | Large modules slow ownership | Multiple Daedalus modules exceed 250 pure LOC, including execution/advisory/graph modules | Decompose when touched; avoid new dumping grounds |
| M-20260613-08 | Credential failure continuation | Prior finding: credential resolution warning can continue in execution lane | Fail closed where credentials are required |
| M-20260613-09 | Startup evidence guard narrowness | Prior finding: evidence ledger guard fires mainly at app factory level | Enforce at every production repository construction seam |
| M-20260613-10 | Thread/session shutdown joins | Prior finding: session runner lacks robust join/timeout | Add bounded stop/join and double-stop tests |
| M-20260613-11 | Cold-start data warmup | Prior finding: paper strategy subscribes without `request_bars()` warmup | Add warmup if indicators become authority-bearing |
| M-20260613-12 | Wall-clock timing in streaming surfaces | Daedalus streaming aggregator uses `time.time()` for elapsed calculations | Use monotonic time for elapsed durations |
| M-20260613-13 | URL transport hardening | Prior finding: `urllib.request.urlopen` without explicit SSL context | Prefer `httpx`/explicit SSL context |
| M-20260613-14 | Lifecycle status duplication | Prior finding: status and lifecycle_status can drift | Collapse to one authoritative state |

## LOW findings

| ID | Area | Evidence | Action |
|---|---|---|---|
| L-20260613-01 | FastAPI `on_event` deprecation | Builder still has startup decorator surfaces | Migrate to lifespan when touched |
| L-20260613-02 | Telegram `as_legacy_dict()` | `nautilus_runtime/live/telegram_gateway/events.py:24-35` | Remove after typed consumers migrate |
| L-20260613-03 | Topic alias mapping | `topic_stream_mapping.py:58-61,105-112` | Add owner/expiry for each alias |
| L-20260613-04 | Probability model fallback | `allow_heston_fallback=True` in config | Log/model-switch evidence when fallback activates |
| L-20260613-05 | TUI naive local time | `streaming/tui.py` uses `datetime.now()` | Use timezone-aware UTC |
| L-20260613-06 | Historical docs in semantic search | Archived NT 1.223/1.227 references remain | Label as historical evidence only |
| L-20260613-07 | Placeholder readiness claims | Some docs retain placeholder roadmap wording | Keep warning labels until executable evidence exists |
| L-20260613-08 | Paper strategy lifecycle logging | Prior finding: no logs in lifecycle hooks | Add low-noise lifecycle logs |
| L-20260613-09 | Spec-to-strategy flow | Prior finding: flow not obvious to new agents | Add short architecture diagram when touched |

## NautilusTrader alignment review

- **Adapter structure**: Official NT adapter docs require a Rust core for HTTP/WebSocket/parsing/performance-sensitive operations plus a Python integration layer. Daedalus has Rust adapter crates, but Python adapter surfaces still need per-venue evidence before production claims.
- **Data evidence**: Official Data Testing Spec says adapters must pass supported `DataTester` subsets; groups 1-4 are baseline data compliance. Daedalus has readiness definitions and some tests, but no complete per-venue DataTester artifact matrix.
- **Execution evidence**: Official Execution Testing Spec says adapters must pass supported `ExecTester` subsets; groups 1-5 are baseline execution compliance, and reconciliation should be enabled for state consistency. Daedalus live execution remains guarded and cannot claim readiness without these artifacts.
- **Live runtime**: Rust-backed PyO3 adapter evidence should prefer `LiveNode`/factory registration where applicable; Python `TradingNode` paths must be labeled integration-specific and bounded.
- **No blocking / no hidden execution**: AI, Telegram, persistence, and evidence surfaces remain downstream; no reviewed AI/LangGraph/EvoMap sidecar was found with execution authority.

## Semantic legacy / deprecation closure inventory

| Item | Status | Evidence | Closure action |
|---|---|---|---|
| `legacy_menu_service` filename/path | Closed | `tests/test_active_code_legacy_symbol_guard.py` asserts absence | Keep absent |
| Retired CLI modes (`full`, `bot_only`, `price_worker`, `paper`, `run_solo`) | Closed | `tests/test_runtime_cli_legacy_modes_removed.py` | Keep parser strict |
| Redis stream legacy closure | Closed | `tests/test_redis_stream_legacy_closure.py` | Keep closed |
| `PostgresWorkflowRepository` naming drift | Closed | Builder deprecation inventory / `workflow_spine` comment | Do not reintroduce alias |
| `allow_legacy_fixture_refs` | Closed | Strict fixture-ref tests remain | Keep strict scoped artifact refs |
| Telegram `menu_service` compatibility lifecycle | Active shim | `telegram_gateway/menu_service.py:23-28` | Add owner/expiry and remove after callers migrate |
| `TelegramDownstreamEvent.as_legacy_dict()` | Active shim | `telegram_gateway/events.py:24-35` | Replace with typed canonical serialization |
| Topic alias mapping | Active transitional alias | `topic_stream_mapping.py:58-61,105-112` | Add owner/expiry per alias |
| FastAPI `on_event` | Active deprecation | Builder FastAPI startup surfaces | Migrate to lifespan context |
| Builder NT 1.227 vs Daedalus NT 1.228 | Active drift | Builder/Daedalus `pyproject.toml` pins differ | Align or document migration deadline |
| DataTester/ExecTester artifacts | Gap | Daedalus readiness specs exist, but artifact matrix incomplete | Gate adapter claims behind executable evidence |
| Rust paper execution placeholder / live claim boundary | Active guard | Existing ledgers say paper/forward-paper only | Preserve no-live-order claim until proven |

## Security summary

- **No hardcoded production secrets found** in reviewed source surfaces; `.env.example` uses placeholder token/key names.
- **Active HIGH security risks**: Redis fail-open behavior, schema interpolation hardening, and missing-health default-to-healthy behavior.
- **Positive controls**: Secret redaction regex exists in promotion evidence actor; execution live startup validates readiness IDs; AI lane rejects authoritative topic publication; Telegram formatter avoids claiming order status without execution reports.

## Required priority order

1. Fix fail-open safety defaults: Redis rate limiter and Daedalus graph-runner missing telemetry.
2. Fix silent order-processing exception swallowing in adapters.
3. Fix pipeline compile exception evidence loss.
4. Harden schema identifier handling.
5. Build per-venue DataTester/ExecTester/reconciliation evidence before production adapter claims.
6. Close or time-box active compatibility shims.

Master reconciliation — catalog-backed Nautilus replay

---

## 2026-06-17 Deep Code Review — TradeHUD Seam + Regression Audit

### Review authority and scope

- **Repo reviewed**: `/home/mok/projects/nautilus_builder` on `master` at `34c6e7b`.
- **Reference repo**: `/home/mok/projects/Nautilus-Daedalus` (Builder-side contract alignment only).
- **Delta since last review**: commits `7d67bb3`..`34c6e7b` added the full TradeHUD observational-monitor seam plus an `init-deep` AGENTS.md hierarchy pass. The pre-existing findings (2026-06-13) remain in effect above; this section covers the TradeHUD seam and the regressions it introduced.
- **Independent review lane status**: `multi_agent_v1` (native code-reviewer + architect subagent lanes) is **unavailable in this Codex environment** (`unsupported call`). This review is therefore single-lane, performed by the leader agent directly against current source and test evidence. Per the code-review skill contract, dual-lane evidence is NOT satisfied; treat the synthesis below as single-lane with that caveat.
- **Authoritative refs re-checked (2026-06-17)**:
  - NautilusTrader local pin: `nautilus_trader==1.227.0` (`pyproject.toml:12`). Latest upstream release remains `v1.228.0`. Drift persists (1 patch behind).
  - EvoMap/evolver, LangChain, LangGraph: unchanged since 2026-06-13 check; AI surfaces remain advisory/process-only in code.

### Executive synthesis (2026-06-17)

- **Final recommendation**: `REQUEST CHANGES` — two new HIGH regressions from the TradeHUD standalone merge break the test contract; do not treat `master` as green/merge-ready for CI gating until fixed.
- **Architectural status**: `WATCH` — the TradeHUD seam is well-bounded (read-only, Python-contract-first, defensive SSE redaction) and does not introduce execution authority. Residual risks are the stale snapshot, the removed root page, and the oversized `redis_adapter.py`.
- **Positive**: missing!=zero contract is enforced by 174 tests; TS types mirror Python models; SSE route redacts sensitive keys; no order/credential authority leaked into the monitor.

---

### Status updates to prior findings

| Prior ID | Status (2026-06-17) | Evidence |
|----------|--------------------|----------|
| H-01 (integration test failure) | **FIXED** | `pytest tests/integration/test_catalog_replay_ledger_updates.py` → 1 passed |
| H-02 (pipeline exception swallowing) | **STILL ACTIVE** | `packages/pipeline/service.py:68` still `except Exception:` with no detail capture |
| H-03 (Redis rate limiter fail-open) | **PARTIALLY ADDRESSED** | `packages/auth/redis_rate_limit.py:29` added `fail_closed: bool = False` param; default still open, but production callers can opt into closed. Default behavior unchanged. |
| H-04 (schema interpolation) | **STILL WATCH** | Unchanged; `safe_postgres_identifier` guard remains the sole defense |
| on_event deprecation | **STILL ACTIVE** | `services/api/fastapi_app.py:206-207` still uses `@app.on_event("startup")` |

---

### NEW HIGH (2) — TradeHUD standalone merge regressions

#### H-20260617-01: OpenAPI snapshot test stale after TradeHUD route additions
- **File**: `tests/api/test_openapi_snapshot.py:22` vs `tests/api/openapi_snapshot.json`
- **Issue**: The snapshot was not regenerated when the TradeHUD routes were added. The test reports:
  `added={'/api/tradehud/events/replay', '/api/tradehud/stream', '/api/tradehud/snapshot', '/api/tradehud/health'}`
- **Risk**: CI cannot report green; the snapshot contract is broken; any future route change is masked by this pre-existing failure.
- **Fix**: Regenerate the snapshot: `python3 -c "import json; from services.api.fastapi_app import create_fastapi_app; app=create_fastapi_app(); json.dump(app.openapi(), open('tests/api/openapi_snapshot.json','w'), indent=2, sort_keys=True)"` then commit. Verify the new paths are intentional.
- **Category**: Bug / CI

#### H-20260617-02: 11 web contract tests fail — root `app/page.tsx` removed by standalone merge
- **Files**: `tests/web/test_app_shell_contract.py`, `test_antd_operator_ui_contract.py`, `test_ai_copilot_frontend.py`, `test_config_ui_contract.py`, `test_execution_lane_ui_contract.py`, `test_frontend_data_wiring.py`, `test_job_console_frontend.py`, `test_results_dashboard_frontend.py`, `test_sectioned_operator_ui.py` (11 test cases total)
- **Root cause**: The `feat/tradehud-standalone` merge removed the root `apps/web/app/page.tsx`. The route group `app/(builder)/` is URL-transparent (parentheses), so the *app* still resolves `/` to `app/(builder)/page.tsx` at runtime — but the contract tests assert the presence of a literal `apps/web/app/page.tsx` file (file-existence + content checks), which no longer exists.
- **Evidence**: `find apps/web/app -name "page.tsx"` shows pages only under `(builder)/` and `tradehud/`; no root `page.tsx`.
- **Risk**: CI reports 11 failures; the operator-shell contract is unverifiable; the intent of the standalone merge (decouple TradeHUD from the builder shell) is sound but the contract tests were not updated.
- **Fix** (pick one):
  1. **Preferred**: Add back a thin root `apps/web/app/page.tsx` that re-exports or redirects to the builder shell, restoring the file the tests assert against; OR
  2. Update the 11 web contract tests to assert against `app/(builder)/page.tsx` and document the route-group restructure.
- **Category**: Bug / Alignment

---

### NEW MEDIUM (5) — TradeHUD seam

#### M-20260617-01: `redis_adapter.py` is 843 LOC in a single module
- **File**: `packages/tradehud_contracts/redis_adapter.py` (843 LOC)
- **Issue**: Exceeds the 250 LOC ceiling the repo applies elsewhere (Daedalus precedent, `execution_lane` flagged the same way). Contains 13 `_parse_*` functions, the `RedisStreamAdapter` class, health tracking, and seed logic in one file.
- **Risk**: Review difficulty, merge-conflict surface.
- **Fix**: Split into `redis_adapter/{_parsers.py, _snapshot.py, adapter.py, _health.py}` once the module stabilizes. Add a LOC-boundary test like `execution_lane` should have.
- **Category**: Maintainability / Architecture

#### M-20260617-02: `_LEGACY_STREAM_MAP` has no owner/expiry
- **File**: `packages/tradehud_contracts/config.py:14`
- **Issue**: The `nautilus:tradehud:*` legacy stream namespace map is a backward-compat shim selected when `stream_namespace="nautilus_tradehud"`. It has no documented owner, expiry, or closure test asserting it can eventually be removed.
- **Risk**: Shim drift — the pattern flagged across the repo (Telegram menus, topic aliases). Inconsistent with the owner/expiry discipline applied elsewhere.
- **Fix**: Add an `# OWNER: <team> EXPIRY: <date>` header comment and a test that asserts the legacy map is only reachable via explicit env opt-in.
- **Category**: Legacy / Maintainability

#### M-20260617-03: SSE route has no auth dependency
- **File**: `services/api/routes/tradehud_sse.py`
- **Issue**: The route declares "Read-only. No order execution authority." and redacts sensitive keys, but does not wire an auth `Depends(...)` the way other route modules do. In a production deployment behind the API, any client that can reach `/api/tradehud/stream` can subscribe to live ND runtime state (positions, orders, PnL).
- **Risk**: Information disclosure of account/position data to unauthenticated clients if the route is exposed without a gateway auth layer.
- **Fix**: Add the same auth dependency the other read routes use (or document explicitly that TradeHUD SSE is intended to sit behind the existing audit/auth middleware and verify the middleware covers it). Confirm `services/api/middleware.py` applies to the tradehud router.
- **Category**: Security

#### M-20260617-04: Broad `except Exception` in `redis_adapter` parse paths (5 sites)
- **File**: `packages/tradehud_contracts/redis_adapter.py:277, 686, 713, 721, 756`
- **Issue**: Five broad exception catches. Most are defensible (JSON fallback → `[]`; `aclose()` swallow; XREAD → log + mark disconnected), but line 277 (`_json.loads` → return `[]`) silently drops malformed position/order arrays with no log.
- **Risk**: Malformed ND payloads silently produce empty position/order lists, which the UI renders as "no positions" — a misleading observational state.
- **Fix**: Add a `logger.debug("malformed %s payload: %s", ..., exc)` at line 277 so malformed payloads are at least diagnosable. The other four sites are acceptable as-is.
- **Category**: Maintainability / Observability

#### M-20260617-05: `tradehud_seed_redis.py` lacks a production-guard
- **File**: `scripts/tradehud_seed_redis.py`
- **Issue**: Header says "LOCAL DEVELOPMENT ONLY" but there is no runtime guard rejecting a non-local Redis URL (e.g., it will seed any `REDIS_URL` it's given).
- **Risk**: Operator mistake seeds a shared/production Redis with mock data.
- **Fix**: Add a guard that refuses to run unless `REDIS_URL` resolves to `localhost`/`127.0.0.1` or an explicit `--i-know-this-is-not-local` flag is passed. Mirror `tradehud_replay_nd_fixtures.py`'s local-only intent.
- **Category**: Security / Safety

---

### NEW LOW (3)

#### L-20260617-01: Two `@deprecated` TS files are now dead code
- **Files**: `apps/web/lib/apiClient.ts` (`@deprecated Use apiFetch...`), `apps/web/components/shell/OperatorAppShell.tsx` (`@deprecated Use BuilderShell`)
- **Issue**: `grep` confirms zero remaining importers outside the files themselves. They are pure dead code.
- **Fix**: Delete both files (reversible via git). Remove the deprecation comments with them.
- **Category**: Maintainability / Legacy closure

#### L-20260617-02: `CATALOG_BACKED_REPLAY_SMOKE_MODE` duplication across 3 ledgers
- **Issue**: The reconciliation phrase must be hand-maintained in `structure.md`, `findings.md`, and `handguard.md` simultaneously, enforced by one integration test. Duplicated invariant.
- **Fix**: Acceptable as a documentation-contract pattern, but add a comment at each occurrence pointing to the enforcing test so future editors know it's load-bearing.
- **Category**: Maintainability

#### L-20260617-03: NT version drift persists (1.227.0 vs 1.228.0)
- **Issue**: Unchanged since 2026-06-13. One patch behind upstream.
- **Fix**: Run the test suite against 1.228.0 and bump, or document an intentional pin deadline.
- **Category**: Alignment

---

### Updated legacy / deprecation closure inventory (2026-06-17)

| Item | Status | Evidence | Action |
|------|--------|----------|--------|
| `_LEGACY_STREAM_MAP` (tradehud_contracts) | **NEW active shim** | `config.py:14` | Add owner/expiry |
| `apiClient.ts` `@deprecated` | **Now dead code** | zero importers | Delete |
| `OperatorAppShell.tsx` `@deprecated` | **Now dead code** | zero importers | Delete |
| `legacy manifest` (artifact_bundle.py:39) | Active backward-compat | documented | Keep + owner/expiry |
| `Legacy protocol: put/get` (s3_store.py:112) | Active backward-compat | documented | Keep + owner/expiry |
| Prior closures (postgres workflow repo, demo tokens, browser creds, docker, on_event) | Unchanged from 2026-06-13 table above | see above | — |

---

### Updated priority order (2026-06-17)

1. **Fix H-20260617-01** — regenerate OpenAPI snapshot (unblocks CI).
2. **Fix H-20260617-02** — restore root `app/page.tsx` or update the 11 web contract tests (unblocks CI).
3. **Fix H-02** — capture pipeline compile exception message (still open from 2026-06-13).
4. **M-20260617-03** — confirm TradeHUD SSE route is covered by auth middleware.
5. **M-20260617-05** — add localhost guard to `tradehud_seed_redis.py`.
6. **L-20260617-01** — delete the two dead deprecated TS files.
7. Prior H-03 (rate-limit default), H-04 (schema interp), architecture WATCH items — carry forward.

Master reconciliation — catalog-backed Nautilus replay


---

## Backlog closure pass — 2026-06-21 (segmented execution)

Reference: this pass closes the 2026-06-21 Fix Backlog (P0–P4) plus the active
findings above, segment by segment, TDD (red -> green) per segment.

### Baseline captured (2026-06-21)
- 1816 tests collected; **16 failing** on `master`:
  - `test_openapi_snapshot::test_openapi_schema_matches_snapshot` (P1-1 / H-20260617-01)
  - `test_route_auth_scope::test_every_registered_api_route_is_auth_tested` (P0-1)
  - `test_strategies::test_strategy_detail_frontend_pages_are_present` (web contract)
  - `test_nd_freshness_contracts::test_stale_threshold` + `::test_stale_after_threshold`
    (root cause: `"trades"` logical stream missing from both stream maps in
    `packages/tradehud_contracts/config.py`; consumed by `redis_adapter.py:783`
    and the reducer but never registered -> tracker returns `unknown`)
  - 11 `tests/web/*` contract tests (P1-2 / H-20260617-02: root `app/page.tsx`
    removed by the standalone merge)

### S1 — P0-2: `/api/evidence` NameError CLOSED
- **File**: `services/api/fastapi_app.py:355-359`
- **Bug**: route bound `_context` (underscore = intentionally unused) but the
  body referenced `context.project_id`, raising `NameError` for every
  authenticated caller.
- **Fix**: rename `_context` -> `context` so the success path uses the resolved
  project scope.
- **Tests**: `tests/api/test_evidence_list_route.py` (2 cases)
  - authenticated GET /api/evidence returns 200 (was NameError->500)
  - returned evidence is project-scoped; cross-project evidence does not leak
- **Regression check**: `tests/api/test_evidence_summary.py`,
  `test_fastapi_app.py`, `test_security_hardening.py` green; only the pre-existing
  `test_every_registered_api_route_is_auth_tested` (P0-1) remains red.


### S2 — P0-1: TradeHUD routes now route-level auth + rate-limit gated CLOSED
- **Files**: `services/api/fastapi_app.py:284-322` (4 routes), test seam
  `tests/api/test_fastapi_app.py` + `tests/api/test_route_auth_scope.py` +
  new `tests/api/test_tradehud_route_auth.py`.
- **Bug**: `/api/tradehud/{snapshot,health,events/replay,stream}` were registered
  without `require_context(...)`; access depended on middleware only, the route
  itself enforced nothing, and the stream could start before auth.
- **Fix**: every TradeHUD route now calls `require_context(authorization)` and
  early-returns the auth/rate-limit error, identical to the other `/api/*` routes.
  The SSE route performs the check BEFORE constructing the `StreamingResponse`, so
  a stream never starts for an unauthenticated caller.
- **Contract**: the 4 routes are registered in `PROTECTED_API_ROUTE_CALLS`
  (`test_route_auth_scope.py`), so
  `test_every_registered_api_route_is_auth_tested` now passes (was failing because
  the routes were registered but not in the expected/auth-tested set).
- **Tests** (`tests/api/test_tradehud_route_auth.py`, 4 cases): missing-auth -> 401
  for all 4; authenticated -> 200 for all 4; deny-all limiter -> 429 for all 4 keyed
  on `user:project`; unauthenticated stream returns 401 and does NOT construct a
  streaming response.
- **Regression check**: `tests/api/` + `tests/tradehud_contracts/` +
  `tests/tradehud_redis/` — only the pre-existing baseline failures remain
  (OpenAPI snapshot P1-1, web contract, trades-stream freshness). No new failures.


### S3 — P0-3: pipeline compile failures now preserve redacted root cause CLOSED
- **Files**: `packages/pipeline/service.py` (PipelineStep + compile except), new
  `packages/pipeline/redaction.py`.
- **Bug**: `run_pipeline` wrapped `compile_strategy_spec` in `except Exception:`
  and recorded only `PipelineStep(name="compile", status="failed")`. No exception
  type, message, or detail survived, so operators could not diagnose spec
  validation vs compiler vs filesystem vs Nautilus API drift vs runtime errors.
- **Fix**:
  - `PipelineStep` gains optional `detail: str | None = None` and
    `error_type: str | None = None` (defaults keep `extra="forbid"` and every
    existing caller/serialized snapshot valid).
  - new `packages/pipeline/redaction.py::redact_error_message` scrubs Redis URL
    passwords, bearer tokens, api_key/password/secret/token assignments, while
    preserving diagnostic text and host/port.
  - the compile `except` now captures `as exc`, records `error_type=
    type(exc).__name__` and `detail=redact_error_message(str(exc))`.
- **Tests** (`tests/pipeline/test_pipeline_compile_error_detail.py`, 4 cases):
  forced RuntimeError preserves error_type + detail; ValueError with embedded
  secrets redacts them (redis pw, api_key, bearer, password) while keeping the
  root-cause sentence; validation failure still skips compile cleanly with
  detail/error_type None; extra="forbid" still rejects unknown fields.
- **Regression check**: `tests/pipeline/` + `tests/api/test_pipeline_run.py` ->
  20 passed.


### S4 — P1-1 OpenAPI snapshot + P1-2 web contracts CLOSED
- **P1-1 / H-20260617-01 (OpenAPI)**: regenerated `tests/api/openapi_snapshot.json`
  from `create_fastapi_app().openapi()` (52 paths). The snapshot now records the 4
  TradeHUD routes AND their `authorization` header params + security requirements
  (proof the S2 auth fix is reflected in the schema contract).
  `test_openapi_schema_matches_snapshot` passes (was failing: 4 tradehud paths
  were `added`).
- **P1-2 / H-20260617-02 (web contracts)**: the `feat/tradehud-standalone` merge
  had moved all builder pages into a `(builder)` route group and dropped the root
  `app/page.tsx`, breaking 11 file-location contract tests. Root cause analysis:
  the `(builder)` group is URL-transparent and gained nothing, while the contract
  tests assert public flat route file locations (`app/page.tsx`,
  `app/strategies/page.tsx`, `app/layout.tsx` must contain `BuilderShell`, etc.).
  Fix: flatten the route group back into `app/` (22 files moved one level up,
  relative imports recomputed by file depth, same-dir `./` and bare package
  imports preserved) and merge the group's `<BuilderShell>` wrapper into the root
  `app/layout.tsx`. TradeHUD remains standalone (`app/tradehud/page.tsx` with
  `TradeHudShell`, untouched). Verified:
  - `tests/web/` + `tests/api/test_strategies.py` -> 78 passed (was 11 failing).
  - `tsc --noEmit` in `apps/web` -> exit 0 (imports are type-correct after the
    relative-path recompute).
- **Regression check**: `tests/api/` + `tests/web/` -> 265 passed, 1 skipped.


### S5 — P1-3/P1-4/P1-5: rate-limit fail-closed default, lifespan, session stop CLOSED

**P1-3 (RedisRateLimiter fail-closed default)**:
- `packages/auth/redis_rate_limit.py`: constructor default flipped
  `fail_closed: bool = False` -> `True`; module + class docstrings rewritten to
  state fail-closed is the safe default and fail-open is local/dev opt-in only.
- `create_fastapi_app` already passed the correct value so production behavior is
  unchanged; the change removes the footgun of bare construction failing open.
- `test_fails_open_when_redis_unavailable` (existing) now explicitly passes
  `fail_closed=False`, documenting the opt-in.
- New `tests/auth/test_redis_rate_limit_default.py` (2 cases): default construction
  denies when Redis is down; fail-open requires explicit `fail_closed=False`.

**P1-4 (FastAPI on_event -> lifespan)**:
- `services/api/fastapi_app.py`: replaced `@app.on_event("startup")` with an
  `@asynccontextmanager` lifespan that calls the same `_revalidate_evidence_storage`
  belt-and-suspenders guard, passed via `FastAPI(..., lifespan=_builder_lifespan)`.
  Identical fail-closed behavior; removes the deprecated-hook warning.
- `_FakeFastAPI` stub accepts `lifespan=` and records `lifespan_passed`/`on_event_used`.
- New `tests/api/test_fastapi_lifespan.py`: asserts the app is built with a lifespan
  handler and does NOT register an on_event hook.

**P1-5 (NativeTradingNodeSessionRunner.stop idempotency)**:
- `packages/execution_lane/sessions.py`: `TradingNodeStopResult.status` Literal
  extended with `NOT_FOUND` and `STOP_TIMEOUT`; `stop()` now `pop(session_id,
  None)`, returns NOT_FOUND for unknown/double stop (no KeyError), records a
  STOP_TIMEOUT event and skips `dispose()` when the worker thread is still alive
  after the join timeout.
- New `tests/execution_lane/test_native_session_stop.py` (4 cases): unknown
  session -> NOT_FOUND (no crash); double stop -> NOT_FOUND; normal stop calls
  stop+join+dispose with DISPOSED; hung thread -> STOP_TIMEOUT and dispose() not
  called.

- **Regression check**: `tests/auth/` + `tests/execution_lane/` + fastapi/lifespan/
  route_auth_scope/openapi/production_safety -> 189 passed, 1 skipped; the
  on_event deprecation warning is gone.


---

## Master reconciliation — 2026-06-21 backlog closure (ALL P0+P1 CLOSED)

**Suite result**: `pytest -q` -> **1850 passed, 1 skipped, 2 warnings** (baseline
was 1816 collected / 16 failing). +34 new regression tests, 0 failures, 0 errors.

### Closed items (with regression-test evidence)

| Item | Status | Evidence |
|------|--------|----------|
| P0-2 /api/evidence NameError | **CLOSED** | `tests/api/test_evidence_list_route.py` (2) |
| P0-1 TradeHUD route auth + rate-limit; SSE auth-before-stream | **CLOSED** | `tests/api/test_tradehud_route_auth.py` (4); routes in `PROTECTED_API_ROUTE_CALLS` |
| P0-3 pipeline compile error detail + redaction | **CLOSED** | `tests/pipeline/test_pipeline_compile_error_detail.py` (4) |
| P1-1 OpenAPI snapshot | **CLOSED** | regenerated; `test_openapi_snapshot.py` green (4 tradehud paths + security) |
| P1-2 web contracts (11 tests) | **CLOSED** | route group flattened, root `app/page.tsx` restored, `BuilderShell` in layout; `tsc --noEmit` exit 0; 78 passed |
| P1-3 Redis fail-closed default | **CLOSED** | `tests/auth/test_redis_rate_limit_default.py` (2); existing fail-open test now explicit opt-in |
| P1-4 on_event -> lifespan | **CLOSED** | `tests/api/test_fastapi_lifespan.py`; deprecation warning gone |
| P1-5 session stop idempotency | **CLOSED** | `tests/execution_lane/test_native_session_stop.py` (4) |
| P2-1 evidence factory guard | **CLOSED** | `tests/evidence_ledger/test_repository_factory_guard.py` (4) |
| P2-4 SSE prod Redis-unavailable degraded event | **CLOSED** | `tests/tradehud_redis/test_tradehud_sse_redis.py` (+1) |
| P2-5 LLM transport explicit TLS + timeout | **CLOSED** | `tests/ai_builder/test_llm_transport_ssl_timeout.py` (2); S310 removed |
| P2-6 / P2-7 paper strategy lifecycle logging + warmup | **CLOSED** | `tests/execution_lane/test_paper_strategy_warmup_logging.py` (5) |
| P3-1 legacy stream-map owner/expiry/removal-criteria | **CLOSED** | `tests/tradehud_contracts/test_legacy_stream_map_governance.py` (5) |
| P3-3 Rust LiveNode labelled future-only | **VERIFIED** | existing `test_paper_profile_builds_python_tradingnode_plan_without_live_authority` enforces no false availability |
| P3-4 AI advisory-only static guard | **VERIFIED** | existing authority scan + evidence/promotion gates; TradeHUD/AI cannot submit orders |
| P4-1 duplicate status fields | **DOCUMENTED** | ExecutionLaneSession `status`/`lifecycle_status` kept; documented single-source-of-truth intent |
| P4-2 `_installed_nautilus_version` except narrowed | **CLOSED** | Exception -> ImportError |
| P4-3 demo token unmistakable name | **CLOSED** | `EXAMPLE_DO_NOT_USE_BUILDER_TOKEN_2026` in `_DEMO_TOKENS` |
| P4-4 `py.typed` marker | **CLOSED** | `packages/py.typed` (PEP 561) |
| trades stream-map gap (2 freshness tests) | **CLOSED** | `trades` added to both stream maps; `tests/tradehud_contracts` 271 passed |

### Deferred (explicit, behind a green test gate)
- **P2-2** execution_lane module split and **P2-3** tradehud redis_adapter module
  split: large refactors. Behavior is now locked by the green test gate above; the
  splits themselves are a follow-up. A boundary/LOC enforcement test should be added
  when the split lands.

### Production-readiness gate status
All P0 items fixed with regression tests. OpenAPI and web contract tests pass.
Redis fail-closed production behavior is proven by default. TradeHUD routes are
explicitly auth/rate-limit protected. TradeHUD/AI remain downstream/advisory/
read-only and cannot submit orders (authority scan green). Legacy/deprecation shims
have owner, expiry, and closure tests. The remaining production-readiness items
(adapter DataTester/ExecTester/reconciliation evidence per claimed venue) are
unchanged from prior passes and remain the open work to claim full venue green.

---
## 2026-06-21 remaining findings closure (ultragoal pass)

This pass resolves the remaining findings from the 2026-06-21 backlog using TDD.
Historical NT version mentions above (1.227.0 vs 1.228.0) are superseded by this
section: the 1.227.0->1.228.0 drift is now CLOSED (pin upgraded to 1.228.0,
aligned with Nautilus-Daedalus; no API breaks; verified by the version-drift
guard tests passing with the new pin).

### Closed this pass
- **TradeHUD SSE production Redis-unavailable stops after stream_error**: in
  production with `TRADEHUD_FEED_SOURCE=redis` but Redis configured-but-
  unavailable, the SSE generator emitted `stream_error` then fell through into a
  synthetic snapshot, making a broken live feed look alive. After `stream_error`
  the generator now returns; local/dev mock fallback is unchanged.
  (commit: `fix(tradehud): P2-4 production Redis-unavailable SSE stops after
  stream_error`.)
- **Fixture replay LOCAL-DEV-ONLY runtime guard**: `scripts/tradehud_replay_nd_
  fixtures.py` now enforces LOCAL DEV ONLY at runtime — host allowlist, env guard
  (BUILDER_ENV/APP_ENV/ENVIRONMENT), scary override (host check only), and Redis
  URL redaction. (commit: `fix(security): enforce LOCAL-DEV-ONLY runtime guard on
  fixture replay script`.)
- **NautilusTrader 1.227.0 -> 1.228.0 drift**: pin upgraded to the current
  official release, aligned with Daedalus. `engine_contract.py`, `pyproject.toml`,
  `uv.lock` updated; drift-sample tests updated to keep exercising the same minor
  vs patch drift categories. (commit: `fix(deps): upgrade nautilus_trader
  1.227.0 -> 1.228.0 (align with Daedalus)`.)
- **Adapter/readiness overstatement guard**: readiness wording was already
  conservative (live_execution OUT_OF_SCOPE requiring DataTester/ExecTester/
  reconciliation). Hardened with 3 defensive tests so READY cannot be claimed
  without evidence types and production/live-named capabilities can never be READY.
  (commit: `test(readiness): lock evidence-gated invariant`.)

### Already closed in the prior 2026-06-21 pass (still closed)
TradeHUD route auth; evidence-list `context` bug; pipeline redacted compile error
detail; Redis rate-limit fail-closed default; FastAPI lifespan migration; native
TradingNode stop idempotency; legacy stream-map owner/expiry.

### Remaining risks (unchanged)
- Production adapter/live claims still require DataTester/ExecTester/
  reconciliation artifacts per venue/capability; Builder is evidence-gated
  scaffold/contract only.
- Deferred cleanup (locked by green tests): execution_lane module split (P2-2),
  tradehud redis_adapter module split (P2-3).
- Not production-ready / not merge-ready until the handguard gate is satisfied.

---
## 2026-06-21 post-fix rescan — additional improvement

Read-only rescan after the ultragoal closure pass. Suite green at time of
rescan (1873 passed, 1 skipped, 0 failed).

### Closed this rescan
- **SSE staging parity (P2-4 consistency):** `services/api/routes/tradehud_sse.py`
  `_is_production_env()` previously matched only `== "production"`, so in
  `BUILDER_ENV=staging` a configured-but-unavailable Redis feed silently fell
  back to a synthetic snapshot (the exact broken-live-feed-looking-alive failure
  P2-4 was meant to prevent). Extended to treat `staging` and `production` as the
  strict/non-local set, matching the canonical `BuilderEnvironment` (LOCAL /
  STAGING / PRODUCTION). New staging test asserts stream_error + stop; local/dev
  fallback unchanged.

### Tracked follow-ups (architecture, behind a green test gate)
- **R2** `services/api/fastapi_app.py` is ~1090 LOC (app factory + route
  registration + startup + evidence guard in one module). Split candidate.
- **R3** `packages/tradehud_contracts/redis_adapter.py` is ~843 LOC (read/write/
  redaction/normalization/health mixed). This is the deferred P2-3 split;
  behavior is locked by green tests, split is a follow-up.
- Optional: add a `ruff` lint gate to CI (tool installed; currently CI runs only
  `compileall` + pytest + TS typecheck for Python).

### Still NOT production-ready
Adapter/live claims still require DataTester/ExecTester/reconciliation artifacts
per claimed venue/capability. Builder remains scaffold/contract/evidence-gated
only.

---
## 2026-06-21 $omo refactor pass — R2/R3/ruff closed

Module-split and lint-gate refactor ($omo:refactor + $omo:programming), behind the
green test gate (zero regression). Full suite 1881 passed, 1 skipped, 0 failed.

### Closed this pass
- **R3 — redis_adapter split (P2-3):** split the 843-LOC monolith into
  `redis_normalizers.py` (parsers + `parse_stream_entry`), `redis_snapshot_builder.py`
  (`build_snapshot_from_redis`), and a thin `redis_adapter.py` (264 LOC,
  connection/IO only) with backward-compatible re-exports. Locked by 7 new
  module-split invariants (public/internal symbol reachability, size <=400 LOC,
  no parser re-definition in the adapter). tradehud tests 279 passed.
- **R2 — fastapi_app helper extraction:** extracted the pure env/config startup
  helpers (`_strictest_configured_env`, `_cors_origins_from_env`,
  `_validate_startup_policy`, `_register_env_dev_token`, `_env_user_project_context`,
  `_default_ai_audit_store`, `_UNSAFE_DEV_TOKENS`) into `services/api/_app_env.py`;
  fastapi_app re-exports them (backward compat). fastapi_app 1090 -> 1014 LOC. The
  create_fastapi_app route closures (shared closure state) were deliberately left in
  place. tests/api 191 passed.
- **Ruff lint gate:** added `[tool.ruff]` (select E4/E7/E9/F) + a `Lint (ruff)` step
  in `.github/workflows/ci.yml` (backend job). Fixed all 22 pre-existing findings in
  packages/services, including 3 real F821 "Undefined name FastAPI" latent bugs in
  `app_factory.py`/`middleware.py`. `ruff check packages services` is clean.

### Still NOT production-ready
Adapter/live claims still require DataTester/ExecTester/reconciliation artifacts per
claimed venue/capability. Builder remains scaffold/contract/evidence-gated only.

