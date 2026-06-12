# Nautilus Builder — Repository Structure (Deep Review 2026-06-12)

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
│   ├── auth/                    # Auth tokens, middleware, rate limiting
│   ├── backend_runtime/         # Backend runtime models
│   ├── backtest_jobs/           # Backtest job management
│   ├── builder_metadata/        # Version/canonical source
│   ├── catalog_datasets/        # Dataset catalog (DuckDB, Parquet)
│   ├── evidence_ledger/         # Evidence verification (InMemory + Postgres)
│   ├── execution_lane/          # Paper/live TradingNode lifecycle
│   │   ├── config_contract.py   # TradingNodeConfigContract (Pydantic)
│   │   ├── credentials.py       # Credential slot provisioning
│   │   ├── nautilus_runtime.py  # Runtime plan + TradingNode config builder
│   │   ├── paper_strategy.py    # Observational paper strategy (no orders)
│   │   ├── sessions.py          # Session lifecycle (start/stop/report)
│   │   └── adapter_config_builders.py  # Binance/Bybit adapter config wiring
│   ├── llm_config/              # LLM provider configuration
│   ├── pipeline/                # Pipeline orchestration
│   ├── readiness/               # Readiness matrix (v4 capability model)
│   ├── research_jobs/           # Research job management
│   ├── strategy_compiler/       # Deterministic spec → artifact bundle
│   ├── strategy_registry/       # Strategy listing/approval/clone
│   ├── strategy_spec/           # Strategy spec models (v1 + microstructure_v1)
│   ├── strategy_validation/     # Authority rules, validators, source health
│   └── workflow_spine/          # SQLite/Postgres workflow repository
├── services/
│   ├── api/                     # FastAPI application
│   │   ├── fastapi_app.py       # App factory (production fail-closed)
│   │   ├── routes/              # API routes (health, strategies, execution_lane, evidence, etc.)
│   │   └── middleware.py        # Audit + auth middleware
│   ├── backend_runtime.py       # Backend runtime service
│   └── workers/                 # Execution lane + backtest workers
├── infra/                       # Docker compose, CI workflows
├── tests/                       # 1479 passing contract tests
└── apps/web/                    # Frontend (Ant Design operator UI)
```

## Key Metrics

| Metric | Value |
|--------|-------|
| Python LOC | ~38,600 |
| Test count | 1,479 passed, 1 skipped |
| NT version pinned | 1.227.0 (pyproject) / 1.227.0 (installed) |
| Dependencies | FastAPI, NautilusTrader, Pydantic v2, Redis, Postgres |

## NautilusTrader API Usage

| NT Feature | Usage | Aligned |
|------------|-------|---------|
| TradingNode (Python) | paper_strategy.py, sessions.py | ✅ |
| LiveNode (Rust) | Planned (future_runtime field) | ⚠️ Future |
| StrategyConfig frozen=True | ExecutionLanePaperStrategyConfig | ✅ |
| on_start → instrument null check | paper_strategy checks `if not None` | ✅ |
| subscribe_quote_ticks | paper_strategy uses directly | ⚠️ No warmup bars |
| reconciliation=True | Enforced ≥60min lookback | ✅ |
| risk_engine bypass=False | Literal[False] enforced | ✅ |
| DataTester/ExecTester evidence | Referenced in profile fields | ✅ |
| Credential via env vars | Local .env.execution.local | ✅ |
