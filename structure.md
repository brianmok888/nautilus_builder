# Nautilus Builder Structure Review

**Review date:** 2026-05-28
**Target repository:** `/home/mok/projects/nautilus_builder`
**Reference repository:** `/home/mok/projects/Nautilus-Daedalus`
**Review mode:** `$superpowers:code-review` routed through `$superpowers:nt-review` (primary) with `nt-architect`, `nt-adapters`, `nt-live`, `nt-testing` supporting checks.

## Authoritative references

- NautilusTrader: `nautilus_trader==1.223.0` (pinned in pyproject.toml)
- https://github.com/nautechsystems/nautilus_trader
- https://nautilustrader.io/docs/latest/developer_guide
- https://nautilustrader.io/docs/latest/developer_guide/adapters/
- https://nautilustrader.io/docs/latest/developer_guide/spec_exec_testing/
- Daedalus reference: `/home/mok/projects/Nautilus-Daedalus` (read-only reference for alignment)

## Repository shape

```text
nautilus_builder/
├── packages/                # Canonical Python domain layer (21 packages)
│   ├── strategy_spec/       # Pydantic StrategySpec schema, in-memory repository
│   ├── strategy_validation/ # Hard-rule checks, forbidden refs, raw-code detection
│   ├── strategy_compiler/   # StrategySpec -> compile artifact/profile metadata
│   ├── ai_builder/          # Advisory AI draft provider, audit store
│   ├── backtest_runner/     # NT backtest config builder, engine boundary, result normalization
│   ├── execution_lane/      # TradingNode runtime plan, credential slots, paper strategy
│   ├── lifecycle/           # Draft->Testing->Beta->Final state machine
│   ├── promotions/          # Shadow/evidence-backed promotion contracts
│   ├── workflow_spine/      # Strategy/test workflow lineage, Postgres/Redis persistence
│   ├── runtime_events/      # In-memory, SQLite, Redis event stream seams
│   ├── adapter_registry/    # Backend-approved adapter profiles
│   ├── instrument_registry/ # Backend-approved instruments, data/timeframe/date checks
│   ├── catalog_datasets/    # Parquet dataset registry
│   ├── auth/                # In-memory test token/project-scope model
│   ├── artifact_store/      # Local JSON artifact persistence
│   ├── backend_runtime/     # Backend runtime readiness checks
│   ├── llm_config/          # OpenAI-compatible model configuration
│   ├── nautilus_rule_graph/ # Placeholder NT strategy classes/profiles
│   ├── research_jobs/       # Durable research-job contracts
│   ├── strategy_registry/   # Read-only external strategy registry/import-as-draft
│   ├── system_verification/ # Composed MVP verification report
│   └── ui_contracts/        # Python-backed executable UI contract helpers
├── services/api/            # FastAPI + thin ApiApp routes over packages/*
├── services/workers/        # Backend-owned worker entrypoint stubs
├── apps/web/                # Next.js + Ant Design v6 app shell (~40 TSX components)
├── tests/                   # 401 pytest tests across 20+ test directories
├── doc/                     # Builder source-truth product, hardguard, lifecycle docs
├── docs/                    # Derived superpowers/spec/audit/verification artifacts
├── infra/                   # Local docker-compose, migrations, CI template
├── pyproject.toml           # Python packaging/test manifest
└── DESIGN.md               # UI design source of truth
```

## Builder authority boundary

The product boundary is enforced at multiple layers:

- **Strategy Builder** — authoring, drafting, validation. No venue credentials or runtime handles.
- **Backtest Center** — backend-owned BacktestNode historical replay only.
- **Execution Lane** — backend-owned TradingNode paper/live lifecycle; server-side credential slots; manual/risk gates.
- **Daedalus gate** — external live authority; Builder never holds `submit_order`.

Code-level enforcement:
- `compiler.py` sets `execution_authority=False` for both `backtest` and `signal_preview_only` profiles.
- `promotions/service.py` returns `may_submit_order=False`, `may_create_trade_action=False`.
- `lifecycle/models.py` exposes `live_trading_authority=False`.
- `execution_lane/nautilus_runtime.py` — `NautilusTradingNodeRuntimePlan` uses `Literal[False]` guards for `browser_credentials_allowed`, `credential_inputs_allowed`, `strategy_lane_coupled`.
- `execution_lane/credentials.py` — venue-prefixed env keys only; forbidden bare key names; file restricted to owner read/write.

## Domain package map

| Package | Role | Key files |
|---|---|---|
| strategy_spec | Pydantic StrategySpec schema + in-memory repo | `models.py`, `repository.py`, `schema.py` |
| strategy_validation | Forbidden refs, raw-code patterns, risk/validation requirements | `policy.py`, `validators.py`, `reports.py` |
| ai_builder | Advisory draft provider + persistent audit store | `provider.py`, `service.py`, `models.py` |
| strategy_compiler | StrategySpec → compile artifact + profile metadata | `compiler.py`, `artifacts.py` |
| backtest_runner | NT config builder, engine boundary, result normalization | `config_builder.py`, `nautilus_engine.py`, `runner.py` |
| execution_lane | TradingNode runtime plan, credential slots, paper strategy | `nautilus_runtime.py`, `credentials.py`, `sessions.py`, `paper_strategy.py` |
| lifecycle | Draft → Testing → Beta → Final state machine | `models.py`, `state_machine.py`, `promotion_policy.py` |
| promotions | Evidence-backed promotion/shadow contracts | `models.py`, `service.py` |
| workflow_spine | Strategy/test lineage, Postgres + Redis persistence | `models.py`, `service.py`, `postgres_repository.py` |
| runtime_events | In-memory, SQLite, Redis event streams | `models.py`, `stream.py`, `redis_stream.py` |

## NautilusTrader integration surface

Pinned at `nautilus_trader==1.223.0`. Import points:

| Module | Imports | Usage |
|---|---|---|
| `execution_lane/sessions.py` | `TradingNode`, `TradingNodeConfig`, `LiveExecEngineConfig`, Binance adapter configs/factories | Paper/live TradingNode session lifecycle |
| `execution_lane/paper_strategy.py` | `Strategy`, `StrategyConfig`, `QuoteTick`, `InstrumentId` | No-order paper strategy shell |
| `nautilus_rule_graph/strategy.py` | `Strategy`, `StrategyConfig`, `QuoteTick`, `InstrumentId` | Placeholder strategy profiles |
| `backtest_runner/catalog_replay_smoke.py` | `BacktestNode`, `BacktestRunConfig`, `ParquetDataCatalog`, `TestDataStubs` | Catalog-backed replay smoke |

## Test verification evidence

```bash
python3 -m compileall -q packages services tests
# Clean compile — 0 errors

python3 -m pytest tests/ -q --tb=line
# 401 passed, 5 warnings (Pydantic model name collision with pytest)
```

## NautilusTrader upstream alignment status

| v1.223.0+ change | Builder impact | Status |
|---|---|---|
| `trade_execution` default now `True` | BacktestVenueConfig in `config_builder.py` — not explicitly set | WATCH |
| `fill_limit_at_touch` → `fill_limit_inside_spread` (v1.224) | Builder doesn't use FillModel directly | CLEAR |
| dYdX v3 adapter removed (v1.223) | Builder doesn't reference dYdX | CLEAR |
| `Quantity - Quantity` returns `Quantity` (v1.223) | Builder doesn't do Quantity arithmetic | CLEAR |
| `LiveDataClient` vs `LiveMarketDataClient` | Builder uses Binance adapter factories (correct for v1.223) | CLEAR |
| `InstrumentProvider.load_all_async` required (v1.224) | Builder doesn't implement custom providers | CLEAR |

## Master reconciliation — catalog-backed Nautilus replay

The Builder backtest runner includes `catalog_replay_smoke.py` which exercises `catalog_backed_replay_smoke` against synthetic historical quote ticks. This confirms BacktestNode catalog replay wiring works end-to-end using `TestDataStubs`-generated fixtures — not full trading-production readiness.
