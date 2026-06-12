# Nautilus Builder — Repository Structure (2026-06-12)

## Overview

**nautilus_builder** is a FastAPI-based strategy builder platform for NautilusTrader. It compiles strategy specifications (classic_v1 and microstructure_v1 families) into deterministic artifacts, manages execution lane lifecycle (paper/live), and provides evidence-based promotion gates.

## Architecture

```
nautilus_builder/
├── packages/                    # Core domain packages
│   ├── adapter_registry/        # Adapter discovery and models
│   ├── ai_builder/              # AI-assisted strategy creation (LLM)
│   ├── artifact_store/          # Local JSON + S3 artifact storage
│   ├── audit/                   # Audit event models
│   ├── auth/                    # Auth tokens, TTL+LRU eviction, rate limiting
│   ├── backend_runtime/         # Backend runtime models
│   ├── backtest_jobs/           # Backtest job management
│   ├── builder_metadata/        # Version/canonical source
│   ├── catalog_datasets/        # Dataset catalog (DuckDB, Parquet)
│   ├── evidence_ledger/         # Evidence verification (InMemory + Postgres)
│   ├── execution_lane/          # Paper/live TradingNode lifecycle
│   │   ├── config_contract.py   # TradingNodeConfigContract (Pydantic)
│   │   ├── credentials.py       # Credential slot provisioning (chmod 0600)
│   │   ├── nautilus_runtime.py  # Runtime plan + TradingNode config builder
│   │   ├── paper_strategy.py    # Observational paper strategy (bars + ticks)
│   │   ├── sessions.py          # Session lifecycle (start/stop/report)
│   │   ├── adapter_config_builders.py  # Multi-venue config (Binance + generic fallback)
│   │   └── service.py           # Bounded stores (max_reports, max_sessions)
│   ├── llm_config/              # LLM provider configuration
│   ├── pipeline/                # Pipeline orchestration
│   ├── readiness/               # Readiness matrix (v4 capability model)
│   ├── research_jobs/           # Research job management
│   ├── strategy_compiler/       # Deterministic spec → artifact bundle
│   ├── strategy_registry/       # Strategy listing/approval/clone
│   ├── strategy_spec/           # Strategy spec models (v1 + microstructure_v1, output_mode enforced)
│   ├── strategy_validation/     # Authority rules, validators, source health
│   └── workflow_spine/          # SQLite/Postgres workflow repository (parameterized SQL)
├── services/
│   ├── api/                     # FastAPI application
│   │   ├── fastapi_app.py       # App factory (production fail-closed + startup guard)
│   │   ├── routes/              # API routes
│   │   └── middleware.py        # Audit + auth middleware
│   ├── backend_runtime.py       # Backend runtime service
│   └── workers/                 # Execution lane + backtest workers
├── infra/                       # Docker compose, CI workflows
├── tests/                       # 1512 passing contract tests
└── apps/web/                    # Frontend (Ant Design operator UI)
```

## Key Metrics

| Metric | Value |
|--------|-------|
| Python LOC | ~38,600 |
| Test count | 1,512 passed, 1 skipped |
| NT version | 1.227.0 (pyproject = installed) |
| Dependencies | FastAPI, NautilusTrader, Pydantic v2, Redis, Postgres |

## NautilusTrader API Usage

| NT Feature | Usage | Aligned |
|------------|-------|---------|
| TradingNode (Python) | paper_strategy.py, sessions.py | ✅ |
| StrategyConfig frozen=True | ExecutionLanePaperStrategyConfig | ✅ |
| on_start → instrument null check | paper_strategy checks `if not None` | ✅ |
| Conditional bar/tick subscription | paper_strategy routes by bar_type | ✅ |
| on_stop explicit unsubscribe | paper_strategy has on_stop | ✅ |
| on_reset cleanup | paper_strategy resets counters | ✅ |
| reconciliation=True | Enforced ≥60min lookback | ✅ |
| risk_engine bypass=False | Literal[False] enforced | ✅ |
| Multi-venue adapter configs | Generic fallback for any venue | ✅ |
| DataTester/ExecTester evidence | Referenced in profile fields | ✅ |
| Credential via env vars | Local .env.execution.local (chmod 0600) | ✅ |
