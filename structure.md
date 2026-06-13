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
| NT version | 1.227.0 |
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
- NautilusTrader is the execution/backtest/live runtime authority. Current local pin: `nautilus_trader==1.227.0`; latest official release checked during review: `v1.228.0`.
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
