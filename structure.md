# Nautilus Builder — Repository Structure (Deep Review 2026-06-12)

## Overview

**nautilus_builder** is a FastAPI-based strategy builder platform for NautilusTrader. It compiles strategy specifications (classic_v1 and microstructure_v1 families) into deterministic artifacts, manages execution lane lifecycle (paper/live), and provides evidence-based promotion gates. The companion **Nautilus-Daedalus** repository provides the runtime actors, adapters, advisory infrastructure (EvoMap/LangGraph), and decision engines.

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

Nautilus-Daedalus/
├── nautilus_actors/             # NT Actor implementations
│   ├── trade_decision_actor.py  # StateBundle → TradeAction decision lane
│   ├── evomap_capsule_advisory_actor.py  # EvoMap advisory overlay (non-blocking)
│   ├── gate_actor.py            # Pre-trade gate decisions
│   ├── signal_preview_actor.py  # Signal preview (no orders)
│   ├── promotion_controller.py  # Strategy promotion logic
│   ├── nt_actor_bus.py          # Message bus compatibility layer
│   └── contracts/               # Actor message contracts
├── nautilus_adapters/           # Custom NT adapters
│   ├── adapters/extended/       # Extended adapter (execution + data)
│   ├── adapters/ethereal/       # Ethereal adapter
│   ├── adapters/o1xyz/          # O1XYZ adapter
│   ├── adapters/standx/         # StandX adapter
│   ├── adapters/apex_omni/      # Apex Omni adapter
│   └── adapters/credential_resolution.py  # SecretStr/env credential resolver
├── nautilus_brain/              # ML/AI decision layer
│   ├── advisory/                # EvoMap orchestrator, audit trail, LangGraph
│   ├── contracts/               # TradeAction, StateBundle, EdgeSignal contracts
│   ├── decision_engines/        # PPO, deterministic, hybrid_shadow
│   └── evaluation/              # Orderflow replay, shadow evaluation
├── nautilus_runtime/            # Runtime configuration
├── packages/prediction_market/  # Polymarket prediction models
└── tests/                       # ~3130 tests (UI failures noted)
```

## Key Metrics

| Metric | nautilus_builder | Nautilus-Daedalus |
|--------|-----------------|-------------------|
| Python LOC | ~38,600 | ~55,000+ |
| Test count | 1,479 passed | ~3,130 (some UI failures) |
| NT version pinned | 1.227.0 (pyproject) / 1.227.0 (installed) | 1.228.0 (pyproject) / 1.227.0 (installed) |
| Dependencies | FastAPI, NautilusTrader, Pydantic v2, Redis, Postgres | NautilusTrader, aiogram, LangGraph, LangChain |

## NautilusTrader API Compatibility Matrix

| NT Feature | Builder Usage | Daedalus Usage | Aligned |
|------------|--------------|----------------|---------|
| TradingNode (Python) | paper_strategy.py, sessions.py | N/A (uses Actors) | ✅ |
| LiveNode (Rust) | Planned (future_runtime) | N/A | ⚠️ Future |
| StrategyConfig frozen=True | ExecutionLanePaperStrategyConfig | ActorConfig frozen=True | ✅ |
| on_start → request_bars → subscribe_bars | paper_strategy uses subscribe_quote_ticks | Actors use custom bus | ✅ |
| Cache instrument null check | Checked in paper_strategy | Checked in adapters | ✅ |
| reconciliation=True | Enforced ≥60min lookback | N/A | ✅ |
| risk_engine bypass=False | Literal[False] enforced | N/A | ✅ |
| Actor message bus (publish_signal/publish_data) | N/A | Custom nt_actor_bus | ⚠️ Custom |
| DataTester/ExecTester evidence | Referenced in profile fields | N/A | ✅ |
| Credential via env vars | Local .env.execution.local | credential_resolution.py | ✅ |
