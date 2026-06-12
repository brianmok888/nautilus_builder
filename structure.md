# Nautilus Builder — Repository Structure (2026-06-12)

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
