# Nautilus Builder — Repository Structure (2026-06-13)

## Overview

**nautilus_builder** is a FastAPI-based strategy builder platform for NautilusTrader. It compiles strategy specifications (classic_v1 and microstructure_v1 families) into deterministic artifacts, manages execution lane lifecycle (paper/live), and provides evidence-based promotion gates.

## Architecture

```
nautilus_builder/
├── packages/                    # Core domain packages
│   ├── adapter_registry/        # Adapter discovery and models (138 LOC)
│   ├── ai_builder/              # AI-assisted strategy creation via LLM (678 LOC)
│   ├── artifact_store/          # Local JSON + S3 artifact storage (582 LOC)
│   ├── audit/                   # Audit event models (47 LOC)
│   ├── auth/                    # Auth tokens, TTL+LRU eviction, rate limiting (628 LOC)
│   ├── backend_runtime/         # Backend runtime models (197 LOC)
│   ├── backtest_jobs/           # Backtest job management (435 LOC)
│   ├── backtest_runner/         # NautilusTrader backtest execution (1634 LOC)
│   ├── builder_metadata/        # Version/canonical source (113 LOC)
│   ├── catalog_datasets/        # Dataset catalog (DuckDB, Parquet) (528 LOC)
│   ├── compatibility/           # Cross-version compat helpers (52 LOC)
│   ├── config/                  # Production fail-closed config (119 LOC)
│   ├── errors/                  # Typed error hierarchy (125 LOC)
│   ├── evidence_ledger/         # Evidence verification (InMemory + Postgres) (510 LOC)
│   ├── execution_lane/          # Paper/live TradingNode lifecycle (1905 LOC)
│   │   ├── config_contract.py   # TradingNodeConfigContract (Pydantic)
│   │   ├── credentials.py       # Credential slot provisioning (chmod 0600)
│   │   ├── nautilus_runtime.py  # Runtime plan + TradingNode config builder
│   │   ├── paper_strategy.py    # Observational paper strategy (bars + ticks)
│   │   ├── sessions.py          # Session lifecycle (start/stop/report)
│   │   ├── adapter_config_builders.py  # Multi-venue config (Binance + generic fallback)
│   │   └── service.py           # Bounded stores (max_reports, max_sessions)
│   ├── instrument_registry/     # Instrument lookup by adapter (96 LOC)
│   ├── lifecycle/               # Component lifecycle tracking (112 LOC)
│   ├── llm_config/              # LLM provider configuration (116 LOC)
│   ├── nautilus_rule_graph/     # Deterministic rule graph evaluator (233 LOC)
│   ├── object_storage/          # Generic object storage abstraction (105 LOC)
│   ├── observability/           # Metrics/observability helpers (40 LOC)
│   ├── pipeline/                # Pipeline orchestration (183 LOC)
│   ├── postgres/                # Postgres migrations, repositories (1921 LOC)
│   ├── promotions/              # Promotion gate with evidence requirements (542 LOC)
│   ├── readiness/               # Readiness matrix (v4 capability model) (144 LOC)
│   ├── research_jobs/           # Research job management (118 LOC)
│   ├── runtime_events/          # Runtime event streaming (240 LOC)
│   ├── strategy_compiler/       # Deterministic spec → artifact bundle (583 LOC)
│   ├── strategy_registry/       # Strategy listing/approval/clone (178 LOC)
│   ├── strategy_spec/           # Strategy spec models (v1 + microstructure_v1) (1179 LOC)
│   ├── strategy_validation/     # Authority rules, validators, source health (375 LOC)
│   ├── system_verification/     # E2E system verification (79 LOC)
│   ├── ui_contracts/            # Frontend contract definitions (120 LOC)
│   └── workflow_spine/          # SQLite/Postgres workflow repository (922 LOC)
├── services/
│   ├── api/                     # FastAPI application
│   │   ├── fastapi_app.py       # App factory (production fail-closed + startup guard)
│   │   ├── routes/              # API routes (16 route modules)
│   │   └── middleware.py        # Audit + auth middleware
│   ├── backend_runtime.py       # Backend runtime service
│   └── workers/                 # Execution lane + backtest workers
├── infra/                       # Docker compose, CI workflows
├── tests/                       # 1441 passing tests (1 integration test failing)
├── apps/web/                    # Frontend (Ant Design operator UI)
└── docs/examples/               # Demo scripts
```

## Key Metrics

| Metric | Value |
|--------|-------|
| Python packages | 36 domain packages |
| Total Python LOC (packages/) | ~12,800 |
| Total Python LOC (services/) | ~2,100 |
| Total Python LOC (tests/) | ~23,700 |
| Test count | 1,441 passed, 1 integration failure, 1 skipped |
| NT version | 1.228.0 |
| Dependencies | FastAPI, NautilusTrader, Pydantic v2, Redis, Postgres, boto3 |
| Git branches | master (active), feat/close-builder-gaps-v1, feat/close-builder-gaps-v2 |

## NautilusTrader API Usage

| NT Feature | Usage | Aligned | Notes |
|------------|-------|---------|-------|
| TradingNode (Python) | paper_strategy.py, sessions.py | ✅ | Labelled as Python live/integration-specific per nt-live skill |
| StrategyConfig frozen=True | ExecutionLanePaperStrategyConfig | ✅ | Correctly frozen |
| on_start → instrument null check | paper_strategy checks `if not None` | ✅ | |
| Conditional bar/tick subscription | paper_strategy routes by bar_type | ✅ | |
| on_stop explicit unsubscribe | paper_strategy has on_stop | ✅ | |
| on_reset cleanup | paper_strategy resets counters | ✅ | |
| reconciliation=True | Enforced ≥60min lookback | ✅ | config_contract.py: ge=60 |
| risk_engine bypass=False | Literal[False] enforced | ✅ | |
| Multi-venue adapter configs | Generic fallback for any venue | ✅ | adapter_config_builders.py |
| DataTester/ExecTester evidence | Referenced in profile fields | ✅ | Evidence refs in readiness checks |
| Credential via env vars | Local .env.execution.local (chmod 0600) | ✅ | credentials.py |
| LiveNode (Rust) | Planned via future_runtime field | ⏳ | future_runtime="rust_live_node" placeholder |
| Clock usage (not system time) | sessions.py uses _now_iso() via datetime(UTC) | ⚠️ | See F-03 |

## Daedalus Reference Alignment

| Feature | Daedalus | Builder | Gap |
|---------|----------|---------|-----|
| Rust paper execution authority | RustPaperExecutionAuthority | Not implemented | ⏳ |
| Execution node/strategy module split | <250 LOC per module | execution_lane ~1905 LOC | ⚠️ See F-08 |
| Polymarket/Deribit adapters | Active | adapter_registry only | Design only |
| EvoMap advisory integration | evomap_capsule_advisory_actor | Not present | N/A |
| Telegram observer sidecar | Present | Not present | N/A |

## Master reconciliation — catalog-backed Nautilus replay

The `catalog_backed_replay_smoke` module validates NautilusTrader replay using synthetic historical quote ticks from the catalog_datasets layer. This is an evidence-gate smoke test, not full trading-production readiness.

Environment: `CATALOG_BACKED_REPLAY_SMOKE_MODE=1` enables catalog-backed replay in tests.
## 2026-06-12 Deep Review Inventory Snapshot


Purpose: semantic inventory for the current Builder repo against NautilusTrader and Daedalus alignment.

### Current authority boundaries
- Builder remains a strategy authoring, validation, backtest/replay, promotion, and execution-lane contract system. It is not the venue adapter source of truth.
- NautilusTrader is the execution/backtest/live runtime authority. Current local pin: `nautilus_trader==1.228.0`, aligned with the Nautilus-Daedalus reference repo and the official `v1.228.0` release (the 1.227.0→1.228.0 drift was closed on 2026-06-21).
- `/home/mok/projects/Nautilus-Daedalus` is a reference implementation for Daedalus runtime alignment only, not a vendored dependency.
- AI/EvoMap/LangChain/LangGraph-style flows are advisory/workflow sidecars: they may draft, explain, and record provenance, but must not bypass manual review or execution-lane authority.

### Active reviewed risk seams
| Seam | Current files | Review status |
| --- | --- | --- |
| API startup/security policy | `services/api/fastapi_app.py`, `packages/auth/policy.py` | Strong fail-closed policy, but FastAPI `on_event` migration remains active. |
| Rate limiting | `packages/auth/redis_rate_limit.py` | Production config requires Redis; runtime Redis failure still needs fail-closed proof. |
| Pipeline orchestration | `packages/pipeline/service.py` | Validation/compile/backtest/promotion flow exists; compile exception details are suppressed. |
| Execution lane | `packages/execution_lane/*` | Credentials/manual review/reconciliation contracts are strong; native TradingNode shutdown and module size remain watch items. |
| Adapter/readiness evidence | `packages/adapter_registry`, `packages/backtest_runner`, tests | Backtest/replay smoke exists; DataTester/ExecTester evidence is not present for production adapter claims. |
| Legacy/deprecation inventory | `docs/deprecations`, `docs/superpowers`, `findings.md` | Closed items are tracked; archived Nautilus 1.223/1.227 docs need historical labels. |

### Independent review status
The requested `code-reviewer` and `architect` native lanes were unavailable in this session. Treat `findings.md` as an evidence-backed local review update, not an independent approval artifact.

---

## 2026-06-13 Deep Review Addendum — Nautilus-Daedalus Reference Snapshot

### Scope and authority

This addendum records the latest Superpowers/NT code-review pass over the current Builder ledger repo with `/home/mok/projects/Nautilus-Daedalus` as the implementation reference. It used independent `code-reviewer` and `architect` native lanes plus local inventory scans. Official NautilusTrader documentation remains the trading-system authority; EvoMap/LangChain/LangGraph references are process-only and cannot override Nautilus execution/readiness rules.

Authoritative NT anchors used for this review:

- Adapter guide: Rust core for networking/performance-sensitive operations, Python layer for platform integration, `InstrumentProvider.load_all_async()`, execution reconciliation, mock-server tests, and PyO3 bindings.
- Data Testing Spec: `DataTester` validates adapter data functionality; groups 1-4 are baseline data compliance for supported data types.
- Execution Testing Spec: `ExecTester` validates execution functionality; groups 1-5 are baseline execution compliance for supported capabilities, and reconciliation should be enabled for state consistency.
- Official Hyperliquid adapter tree: the current upstream Rust adapter shape includes `src/`, `examples/`, `test_data/`, `tests/`, `benches/`, and `Cargo.toml`, reinforcing the Rust-first adapter structure expected for production adapter work.

Process-only AI anchors:

- LangGraph's durable, human-in-the-loop, stateful workflow model supports the repo's evidence-ledger and manual-approval posture, but it is advisory orchestration rather than trading authority.
- LangChain/EvoMap references support auditability/provenance patterns only; they must remain downstream of signal/gate/execution contracts.

### Current Nautilus-Daedalus topology observed

```text
/home/mok/projects/Nautilus-Daedalus
├── crates/adapters/               # Rust-first venue adapter crates, including limitless and several CEX/DEX adapters
├── nautilus_adapters/adapters/     # Python adapter integration layers and compatibility shims
├── nautilus_runtime/live/          # signal/gate/execution/runtime orchestration and validation
├── nautilus_runtime/persistence_writer/ # Redis/PostgreSQL archive writer and latency persistence surfaces
├── nautilus_runtime/ai_lane/       # advisory-only AI lane reading archived facts
├── nautilus_runtime/live/telegram_gateway/ # downstream Telegram display/control surface
├── nautilus_actors/                # MessageBus actors and Redis bridge actors
├── nautilus_brain/                 # advisory/research/model pipelines, not execution authority
├── docs/runbooks/                  # runtime process supervision and operational boundaries
└── tests/                          # adapter evidence, runtime, execution, legacy-closure, and contract tests
```

### Runtime authority map

```text
Signal/Gate TradingNode
  -> nd.gate_decision / core.gate_decision
  -> approved intent only: nd.trade_action / core.trade_action
  -> ExecutionLaneStrategy / Execution TradingNode/Profile is the only default submit_order surface
  -> nd.execution_report / execution.report
  -> persistence_writer archives after durable PostgreSQL commit
  -> AI lane and Telegram projection read archived/downstream facts only
```

`run_full_stack` remains a local manifest/dry-run boundary helper, not a production supervisor. `run_execution_lane --mode live` remains blocked unless paper/sim validation, DataTester-style data readiness, ExecTester-style execution readiness, reconciliation readiness, kill-switch/risk/credential evidence, and operator approval records are all present.

### Current-stage evidence matrix

| Area | Status | Evidence / notes | Production claim |
|---|---:|---|---|
| Master reconciliation — catalog-backed Nautilus replay | ✅ Ledger restored | This phrase is intentionally present in all three ledgers; `CATALOG_BACKED_REPLAY_SMOKE_MODE` remains a handguard token. | Documentation contract only |
| Rust/PyO3 adapter standard alignment | ⚠️ Partial | Daedalus has Rust adapter crates, but active adapter evidence is uneven and not every venue has DataTester/ExecTester artifacts. | No full adapter production claim |
| Live execution lane | ⚠️ Guarded | `execution_lane_validation.py` fail-closes live startup without readiness IDs and approval. | No live order-readiness claim |
| Reconciliation | ⚠️ Required gate | NT execution spec expects reconciliation for state consistency; Daedalus keeps this as readiness input. | Not complete until per-venue artifacts exist |
| AI/EvoMap/LangChain/LangGraph sidecars | ✅ Boundary coherent | Advisory/read-only/downstream in code and runbooks. | No execution authority |
| Telegram / aiogram-dialog menus | ⚠️ Active compatibility surface | Telegram gateway remains downstream-only, but menu compatibility shim and legacy serialization helper remain active drift points. | Display/control only, no signal/order authority |
| Semantic legacy closure | ⚠️ Mixed | Closed legacy names and CLI modes are tested; active shims still require owner/expiry. | Keep inventory active |

### Structural risk summary

- Strong lane separation exists, but production-readiness claims remain blocked by missing executable adapter evidence and active HIGH findings.
- The most important architectural risk is fail-open behavior where missing health/rate-limit data is treated as healthy/allowed.
- The most important maintainability risk is continued compatibility shim drift without owner/expiry, especially Telegram menu and topic alias surfaces.
- The most important adapter-alignment risk is claiming Nautilus compliance before each adapter has DataTester/ExecTester/reconciliation evidence matching supported capabilities.

---

## 2026-06-17 Structure Refresh — TradeHUD Seam + AGENTS.md Hierarchy

### What changed since the 2026-06-13 review

The TradeHUD observational-monitor seam landed on `master` (commits `7d67bb3`..`10b5b90`) plus an `init-deep` AGENTS.md hierarchy pass (`34c6e7b`). The pre-existing structure map above remains accurate for the core domain; this section records the delta.

### New: TradeHUD seam (observational ND runtime monitor)

```
nautilus_builder/
├── packages/tradehud_contracts/         # NEW — Python source of truth for ND runtime contract
│   ├── models.py                        #   262 LOC — Pydantic v2 models (SourceFreshnessMeta base)
│   ├── normalizer.py                    #   missing != true_zero normalizer (Redis Stream entries)
│   ├── redis_adapter.py                 #   843 LOC — RedisStreamAdapter (read-only async consumer)
│   ├── service.py                       #   TradeHudService (snapshot provider, mock fallback)
│   ├── config.py                        #   TradeHudRedisConfig (env stream map, URL sanitization)
│   └── mock_data.py                     #   349 LOC deterministic mock fixtures
├── apps/web/lib/tradehud/               # NEW — TS runtime (reducer, feeds, selectors, formatters)
│   ├── reducer.ts                       #   pure reducer(state, event) over TradeHudEvent
│   ├── replay-feed.ts / sse-feed.ts / mock-feed.ts  # FeedController implementations
│   ├── selectors.ts / freshness.ts      # derived views + staleness logic
│   ├── heatmap-buffer.ts / ring-buffer.ts           # bounded buffers
│   └── number-format.ts / time-format.ts            # pure formatters
├── apps/web/components/tradehud/        # NEW — 25 live panel TSX components
│   ├── TradeHudShell.tsx                #   root layout + feed wiring
│   ├── OrderBookLadder.tsx / BookmapHeatmapPanel.tsx / PriceChartOverlay.tsx
│   ├── AccountSummaryPanel.tsx / PositionsPanel.tsx / OpenOrdersPanel.tsx
│   ├── SignalPreviewPanel.tsx / GateDecisionPanel.tsx / TradeActionEvidencePanel.tsx
│   └── RuntimeHealthPanel.tsx / FreshnessBadge.tsx / StatusChip.tsx / HashPill.tsx
├── services/api/routes/tradehud_sse.py  # NEW — 235 LOC SSE gateway (read-only, sensitive-key redaction)
├── tests/tradehud_contracts/            # NEW — 10 ND contract test modules
├── tests/tradehud_redis/                # NEW — 3 redis adapter test modules
├── tests/fixtures/tradehud_nd_contracts/# NEW — 17 ND jsonl fixtures
├── scripts/tradehud_seed_redis.py       # NEW — LOCAL DEV ONLY Redis seeder
├── scripts/tradehud_replay_nd_fixtures.py  # NEW — fixture replay through normalizer+adapter
└── docs/tradehud-{v0-hardening,redis-stream-adapter,nd-runtime-contract-tests,sse-gateway}.md  # NEW runbooks
```

### New: AGENTS.md knowledge hierarchy (init-deep pass, 2026-06-17)

```
./AGENTS.md                                  (updated — 73 LOC)
├── packages/AGENTS.md                       (unchanged)
├── packages/tradehud_contracts/AGENTS.md    (NEW — 29 LOC)
├── services/api/AGENTS.md                   (unchanged)
├── scripts/AGENTS.md                        (NEW — 29 LOC)
├── apps/web/AGENTS.md                       (unchanged)
│   ├── apps/web/components/AGENTS.md        (unchanged)
│   ├── apps/web/components/tradehud/AGENTS.md (NEW — 28 LOC)
│   └── apps/web/lib/tradehud/AGENTS.md      (NEW — 31 LOC)
├── doc/AGENTS.md                            (unchanged)
├── docs/superpowers/AGENTS.md               (unchanged)
└── tests/AGENTS.md
    └── tests/tradehud_contracts/AGENTS.md   (NEW — 30 LOC)
```

### Updated metrics (2026-06-17)

| Metric | 2026-06-13 | 2026-06-17 | Delta |
|--------|-----------|-----------|-------|
| Python packages | 36 | 37 (+tradehud_contracts) | +1 |
| Total files (excl node_modules/.next/.git) | — | 7,619 | — |
| Total LOC (TS+PY+GO+RS+JS) | — | ~1,567,000 | — |
| NT version pin | 1.227.0 | 1.228.0 (aligned with Daedalus + upstream) | drift closed 2026-06-21 |
| TS typecheck (apps/web) | green | green | — |
| AGENTS.md files | 8 | 13 | +5 |

### Master reconciliation — catalog-backed Nautilus replay

`CATALOG_BACKED_REPLAY_SMOKE_MODE` remains the current catalog-backed replay smoke guard token. This phrase is intentionally present in all three ledgers (structure.md, findings.md, handguard.md) and asserted by `tests/integration/test_catalog_replay_ledger_updates.py`.


---

## 2026-06-21 structural changes

- `apps/web/app/`: the `(builder)` route group was flattened back into the root
  `app/` directory (22 pages moved up one level; relative imports recomputed by
  depth; root `app/page.tsx` restored; `BuilderShell` merged into root layout).
  `app/tradehud/` remains standalone (`TradeHudShell`). `tsc --noEmit` is clean.
- `packages/pipeline/redaction.py` (new): redaction helpers for pipeline errors.
- `packages/evidence_ledger/factory.py` (new): environment-guarded repository factory.
- `packages/execution_lane/sessions.py`: `TradingNodeStopResult.status` extended
  with `NOT_FOUND` / `STOP_TIMEOUT`; stop() idempotent.
- `packages/tradehud_contracts/config.py`: `trades` stream added to both maps;
  legacy map has owner/expiry/removal-criteria metadata.
- `packages/auth/redis_rate_limit.py`: default fail-closed.
- `services/api/fastapi_app.py`: TradeHUD routes auth-gated; on_event -> lifespan.
- `packages/py.typed` (new, PEP 561).
- Deferred: execution_lane module split (P2-2) and tradehud redis_adapter module
  split (P2-3) — behavior locked by the green test gate; splits are a follow-up.

---
## 2026-06-21 master reconciliation — remaining findings closure (ultragoal pass)

Reference posture unchanged: NautilusTrader is the execution/backtest/live
authority; AI/LangChain/LangGraph/EvoMap lanes are advisory only. This pass
closed the remaining review findings listed below using TDD (failing test ->
minimal fix -> green) and `$superpowers:test-driven-development`.

### Closed this pass (evidence-gated)
| Item | Status | Fix | Tests |
| --- | --- | --- | --- |
| TradeHUD SSE production Redis-unavailable must stop after `stream_error` (P2-4 tightened) | ✅ CLOSED | `services/api/routes/tradehud_sse.py`: after emitting `stream_error` in production with a configured-but-unavailable Redis feed, the generator now `return`s instead of falling through into a synthetic/mock snapshot. Local/dev mock fallback unchanged. | `tests/tradehud_redis/test_tradehud_sse_redis.py` (tightened production-stops test + new local-dev fallback test). |
| Fixture replay script LOCAL-DEV-ONLY runtime guard | ✅ CLOSED | `scripts/tradehud_replay_nd_fixtures.py`: runtime host allowlist (`localhost`/`127.0.0.1`/`::1`), environment guard (rejects `BUILDER_ENV`/`APP_ENV`/`ENVIRONMENT` in production/prod/staging/stage), scary `--allow-nonlocal-redis-for-fixture-replay` override (host check only; never bypasses the production-env guard), and `redact_redis_url()` for all logs. | `tests/scripts/test_tradehud_replay_nd_fixtures_guard.py` (22 cases). |
| NautilusTrader version drift (1.227.0 -> 1.228.0) | ✅ CLOSED | Upgraded pin to the current official release `1.228.0` (published 2026-06-08), aligning with Nautilus-Daedalus. `packages/backtest_runner/engine_contract.py`, `pyproject.toml`, `uv.lock` updated. No API breaks; verification failures were the version-drift guard firing because the venv was ahead of the declared pin. | `tests/backtest_runner/test_nautilus_dependency_contract.py`, `tests/backtest_runner/test_runtime_minor_drift.py` updated to exercise the same drift categories against the new pin. |
| Adapter/readiness overstatement guard | ✅ CLOSED (wording already conservative; hardened) | Readiness matrix already keeps `live_execution` OUT_OF_SCOPE (requires DataTester/ExecTester/reconciliation), `production_deployment` PARTIAL, and every READY capability declares `required_evidence_types`. Added defensive tests so a future change cannot silently overstate production/live readiness. | `tests/readiness/test_readiness_matrix.py` (+3 overstatement-guard tests). |
| Ledger cleanup | ✅ CLOSED | This section plus parallel closure markers in `findings.md` and `handguard.md`. | — |

### Items already closed in the prior 2026-06-21 pass (still tracked as closed)
TradeHUD route auth; evidence-list `context` bug; pipeline redacted compile error
detail; Redis rate-limit fail-closed default; FastAPI `on_event` -> lifespan;
native TradingNode stop idempotency; legacy stream-map owner/expiry.

### Remaining risks (unchanged, evidence-gated)
- Production adapter/live claims still require DataTester/ExecTester/
  reconciliation artifacts per claimed venue/capability; Builder wording remains
  scaffold/contract/evidence-gated only.
- Deferred cleanup (behavior locked by green tests): execution_lane module split
  (P2-2) and tradehud redis_adapter module split (P2-3).
- Do NOT use "production-ready"/"merge-ready" wording until the
  production-readiness gate in `handguard.md` is satisfied.

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

---
## 2026-06-21 frontend/backend reconciliation ($omo:frontend)

Reconciliation of the frontend API layer against the backend route surface (50
backend routes). Full Python suite 1881 passed, 1 skipped, 0 failed; web contract
tests 75 passed; lib/api.test.ts 12 passed; tsc clean.

### Cleanup — dead artifacts removed
- `apps/web/lib/apiClient.ts` (DELETED): explicitly-`@deprecated` backward-compat
  shim superseded by `api.ts`; zero imports, zero test references.
- `apps/web/components/shell/OperatorAppShell.tsx` (DELETED): superseded by
  BuilderShell; zero component imports, zero test references (contract test
  requires BuilderShell, not OperatorAppShell). Stale CSS comment updated.

### Reconnected missing read-only API
Added `api.ts` helpers + `types.ts` for safe observational backend routes that
previously had no frontend connection (all READ-ONLY, verified live):
- `fetchReadinessMatrix` -> GET /api/readiness (readiness matrix; live_execution
  remains out_of_scope).
- `fetchEvidenceForLineage` -> GET /api/evidence.
- `fetchRuntimeEventsReplay` -> GET /api/runtime-events/replay.
- `fetchWorkflowLineageStatus` -> GET /api/workflow/lineages/{id}/status.
- `fetchWorkflowResultSuggestions` -> GET /api/workflow/results/{id}/suggestions.

### Safety contract enforced (NOT reconnected)
Execution-authority endpoints are deliberately NOT wired to the frontend, per the
hard read-only/advisory contract enforced by `tests/web/test_execution_lane_ui_contract.py`:
- No execution-lane SESSION modeling or lifecycle (start/stop) in the UI. An
  attempted `ExecutionLaneSessionStatus` read-only helper was REVERTED after the
  contract test caught it forbidding `ExecutionLaneSession` in the frontend.
- No `submit_order`, no credential inputs, no session start/stop, no
  `/api/execution-lane/sessions/start`, no worker run-once, no pipeline-mutating
  endpoints.

### Resolved (frontend vitest page tests)
The 7 frontend vitest page tests that previously failed now pass (206 passed |
4 skipped | 0 failed). Root cause was NOT a `next/navigation`/`useRouter` mock
gap; each page test's `vi.mock("...")` module specifier had one extra `../`
relative to the import path the page-under-test uses, so the mock factory never
matched and the real component/`lib/api` rendered (surfacing as `useRouter` /
`invariant expected app router` / `parse URL` errors). Fix: corrected the
`vi.mock` specifier in 7 test files to exactly match the page import path. Pure
test-infrastructure change: no production code, no api.ts/types.ts symbols, no
test assertions weakened, no execution authority wired (execution-lane UI
contract still green). `tsc --noEmit` clean.

### Still NOT production-ready
Adapter/live claims still require DataTester/ExecTester/reconciliation artifacts
per claimed venue/capability.

