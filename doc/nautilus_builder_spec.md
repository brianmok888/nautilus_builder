# Nautilus Builder — Product & System Specification

## 1. Purpose

Nautilus Builder is a user-facing strategy authoring and backtesting workspace.

Users can:

- create strategies visually;
- ask an AI copilot to draft strategy ideas;
- configure data adapter, venue, instrument, timeframe, and historical range;
- run backtests through NautilusTrader;
- inspect logs, metrics, trades, fills, and charts;
- promote approved strategies into Daedalus shadow/signal-preview mode.

The core rule:

```text
UX = authoring and observation surface
NautilusTrader = backtest/runtime truth engine
Daedalus = live signal/gate/control-plane safety layer
run_execution_lane = only live order authority
```

The UX must never become the runtime owner.

---

## 2. Non-Negotiable Runtime Principle

The UX must not block, own, or keep alive backend runtime processes.

The backend must continue running when:

- the browser tab closes;
- the user refreshes the page;
- the WebSocket disconnects;
- the frontend deploys/restarts;
- a mobile client sleeps;
- the terminal panel disconnects.

All important work must be represented as durable backend state:

```text
StrategySpec
BacktestJob
ValidationReport
CompileArtifact
BacktestResult
PromotionRequest
ShadowDeployment
RuntimeEvent
```

Frontend actions create or inspect backend state. They do not hold long-running execution inside the web session.

---

## 3. High-Level Architecture

```text
Browser UX
  ├── Visual Strategy Builder
  ├── AI Strategy Copilot
  ├── StrategySpec Editor
  ├── Adapter/Instrument/Data Config
  ├── Backtest Dashboard
  ├── Result Viewer
  └── Live Terminal / Job Console

API Backend
  ├── Auth/session layer
  ├── StrategySpec CRUD
  ├── Adapter Registry
  ├── Instrument Registry
  ├── Strategy Validator
  ├── Compiler API
  ├── Backtest Job API
  ├── Result API
  └── WebSocket/SSE progress API

Async Runtime
  ├── Job Queue
  ├── Nautilus Backtest Workers
  ├── Result Normalizer
  ├── Artifact Exporter
  ├── Shadow Deployment Controller
  └── Runtime Event Publisher

Storage
  ├── Postgres: specs, jobs, users, results metadata
  ├── Redis Streams: progress/events/logs
  ├── Object storage: artifacts/reports/trade logs
  └── Nautilus data catalog: market data
```

---

## 4. UX Scope

The UX may:

- create and edit `StrategySpec`;
- configure approved adapters and instruments;
- start/cancel queued backtest jobs through backend APIs;
- inspect logs and progress;
- compare results;
- request promotion to shadow mode;
- display Daedalus signal/gate status;
- show terminal-style job output.

The UX may not:

- instantiate arbitrary Python classes;
- call broker/exchange APIs directly;
- hold a runtime process open through browser connection;
- submit orders;
- modify live orders;
- bypass validators;
- bypass Daedalus gate;
- promote a strategy to live without backend policy checks;
- mutate running backend workers directly.

---

## 5. Core Flow

```text
User idea
  ↓
Visual Builder / AI Copilot
  ↓
StrategySpec draft
  ↓
Schema validation
  ↓
Hard-rule validation
  ↓
Compile to safe Nautilus strategy adapter
  ↓
Create BacktestJob
  ↓
Async worker runs NautilusTrader
  ↓
Store BacktestResult + artifacts
  ↓
UX reads results
  ↓
Optional promotion to Daedalus shadow mode
  ↓
Shadow emits StrategySignalPreview only
  ↓
run_gate_engine may evaluate
  ↓
run_execution_lane remains only live order path
```

---

## 6. StrategySpec Contract

The AI builder and visual builder must output structured specs, not raw executable live code.

Example:

```yaml
strategy_id: ema_rsi_pullback_v1
version: 1
created_by: ai_builder
status: draft

mode:
  backtest: true
  live_profile: signal_preview_only

market:
  adapter_id: BINANCE_PERP
  venue: BINANCE
  instrument_id: BTCUSDT-PERP.BINANCE
  bar_type: BTCUSDT-PERP.BINANCE-5-MINUTE-LAST-EXTERNAL
  start: 2025-01-01T00:00:00Z
  end: 2025-06-01T00:00:00Z

indicators:
  ema_fast:
    type: EMA
    input: close
    period: 20

  ema_slow:
    type: EMA
    input: close
    period: 50

  rsi:
    type: RSI
    input: close
    period: 14

rules:
  long_entry:
    all:
      - crossed_above: [ema_fast, ema_slow]
      - gt: [rsi, 52]

  long_exit:
    any:
      - crossed_below: [ema_fast, ema_slow]
      - lt: [rsi, 45]

risk:
  position_size_pct: 0.05
  stop_loss_pct: 0.012
  take_profit_pct: 0.024
  max_hold_bars: 48

validation:
  bar_close_only: true
  no_lookahead_required: true
  requires_backtest_before_shadow: true
```

---

## 7. Adapter and Instrument Selection

The UX should allow adapter/instrument configuration through a backend-approved registry.

Allowed UX fields:

```text
adapter_id
venue
market_type
instrument_id
bar_type
data_type
timeframe
date_range
fee_model
slippage_model
account_type
starting_balance
leverage policy
```

The frontend must not accept arbitrary adapter import paths.

Correct:

```text
User selects BINANCE_PERP
Backend maps BINANCE_PERP → approved adapter profile
```

Incorrect:

```text
User enters my_module.SomeLiveAdapterClass
```

---

## 8. AdapterRegistry

Example:

```yaml
adapters:
  BINANCE_PERP:
    enabled: true
    venue: BINANCE
    asset_class: crypto_perp
    data_modes:
      - historical_bars
      - trade_ticks
      - quote_ticks
      - order_book_delta
      - funding
      - liquidation
    execution_modes:
      backtest: true
      paper: false
      live: false

  DATABENTO_US_EQUITY:
    enabled: true
    venue: DATABENTO
    asset_class: equity
    data_modes:
      - historical_bars
      - trades
      - quotes
      - mbp_10
    execution_modes:
      backtest: true
      paper: false
      live: false
```

The registry is backend-owned.

---

## 9. Backtest Profiles vs Daedalus Live Profiles

Backtest profile:

```text
StrategySpec
  → RuleGraphBacktestStrategy
  → NautilusTrader simulated orders
  → fills/trades/equity/results
```

Daedalus live/shadow profile:

```text
StrategySpec
  → RuleGraphSignalStrategy
  → StrategySignalPreview only
  → run_gate_engine
  → GateDecision
  → run_execution_lane only if approved
```

The same user-authored strategy may have different compilation profiles.

Backtesting may submit simulated orders inside NautilusTrader backtest.

Live/shadow mode may not directly submit orders.

---

## 10. Live Terminal / Job Console

The terminal is a visibility layer, not the owner of the process.

Normal user terminal:

- read-only streaming logs;
- approved commands only;
- no raw shell;
- no SSH;
- no direct worker process control;
- no exchange credentials;
- no arbitrary command execution.

Admin/dev terminal:

- optional sandboxed shell;
- isolated disposable container;
- no production secrets by default;
- audit log required;
- explicit permission gate.

Terminal disconnect must not stop the backend job.

---

## 11. AI Strategy Builder

The AI copilot may:

- draft `StrategySpec`;
- explain strategy logic;
- suggest indicators;
- suggest risk controls;
- generate parameter variants;
- analyze backtest results;
- recommend revisions;
- prepare promotion-readiness reports.

The AI copilot may not:

- write live execution code by default;
- call `submit_order`;
- call `modify_order`;
- call `cancel_order`;
- set leverage directly;
- access broker credentials;
- promote itself to live;
- override validators;
- hide failing results.

AI outputs are advisory until validated and backtested.

---

## 12. Persistence Model

Minimum tables:

```text
users
projects
strategy_specs
strategy_spec_versions
adapter_profiles
instrument_snapshots
data_availability
backtest_jobs
backtest_results
backtest_metrics
backtest_trades
validation_reports
compile_artifacts
runtime_events
promotion_requests
shadow_deployments
```

Large artifacts:

```text
equity_curve.parquet
trades.parquet
fills.parquet
logs.ndjson
validation_report.md
backtest_summary.html
```

---

## 13. Async Job Lifecycle

```text
CREATED
  → VALIDATING
  → VALIDATED
  → COMPILING
  → COMPILED
  → QUEUED
  → RUNNING
  → NORMALIZING_RESULTS
  → SUCCEEDED
```

Failure states:

```text
VALIDATION_FAILED
COMPILE_FAILED
DATA_UNAVAILABLE
BACKTEST_FAILED
CANCEL_REQUESTED
CANCELED
WORKER_LOST
TIMEOUT
```

A frontend disconnect must not change job state.

---

## 14. Realtime Progress

Backend publishes progress events to Redis Streams.

Example event:

```json
{
  "job_id": "bt_20260522_001",
  "stage": "RUNNING",
  "level": "INFO",
  "message": "Processed 2025-03-01 to 2025-03-15",
  "progress_pct": 52.4,
  "timestamp": "2026-05-22T09:30:00Z"
}
```

Frontend subscribes through WebSocket/SSE.

If the frontend reconnects, it replays job state and missed events from backend storage.

---

## 15. Promotion Flow

```text
BacktestResult
  → validation checks
  → no-lookahead report
  → parameter stability review
  → walk-forward / out-of-sample review
  → shadow request
  → shadow deployment
  → StrategySignalPreview only
  → gate observation
  → production candidate review
```

Promotion to live trading is not a UX button. It is a controlled backend workflow.

---

## 16. Success Criteria

MVP is complete when:

1. User can build a simple EMA/RSI strategy visually.
2. UX outputs valid `StrategySpec`.
3. Backend validates allowed blocks and rejects forbidden blocks.
4. User can choose approved adapter/instrument/timeframe/date range.
5. Nautilus backtest worker runs asynchronously.
6. Browser refresh does not stop the job.
7. UX shows progress from persisted backend events.
8. UX shows equity curve, trades, drawdown, win rate, and logs.
9. Strategy can be saved/versioned.
10. Optional shadow deployment emits `StrategySignalPreview` only.
11. No UX or AI path can submit live orders.

---

## 17. Recommended Stack

Frontend:

```text
Next.js
React
TypeScript
TailwindCSS
shadcn/ui
React Flow
Monaco Editor
xterm.js
TradingView Lightweight Charts
Recharts
TanStack Query
Zustand
```

Backend:

```text
FastAPI
Pydantic
SQLAlchemy or SQLModel
Postgres
Redis Streams
Celery/RQ/Arq worker queue
NautilusTrader workers
Docker sandbox workers
Object storage
Parquet data catalog
```

Runtime principle:

```text
API returns job IDs.
Workers do the work.
UX observes and controls through durable backend APIs.
```

## 18. Builder Lifecycle and Versioning

The builder uses a development-style lifecycle:

```text
Draft → Testing → Beta → Final
```

Lifecycle rules are defined in:

```text
nautilus_strategy_lab_lifecycle_versioning.md
```

Important boundary:

```text
Final does not mean direct live execution.
Final means a frozen approved strategy release eligible for controlled Daedalus production-candidate flow.
```

Stage summary:

```text
Draft   = editable idea/spec stage
Testing = Nautilus backtest/research stage
Beta    = shadow/paper/signal-preview candidate stage
Final   = frozen approved release
```

All tested, beta, and final versions must be immutable. New changes require cloning into a new Draft version.

## 20. Repository and Dependency Architecture

Official NautilusTrader should remain an upstream dependency, installed via pip/uv and pinned by version.

Recommended dependency direction:

```text
official nautilus_trader package
      ↑                     ↑
      │                     │
Nautilus-Daedalus      Nautilus Builder
      ↑                     │
      └──── contracts/events/API ────┘
```

Rules:

```text
Nautilus-Daedalus installs nautilus_trader.
Nautilus Builder installs nautilus_trader.
NautilusTrader does not install or contain Daedalus.
NautilusTrader does not install or contain Nautilus Builder UX.
Nautilus Builder integrates with Daedalus through explicit contracts, not deep runtime coupling.
```

The same pinned NautilusTrader version should be used by both Daedalus and Nautilus Builder to reduce research/live drift.

Detailed dependency guidance is defined in:

```text
nautilus_strategy_lab_repo_dependency_architecture.md
```

## 21. Existing Strategy Registry

The UX should read existing strategies through a backend strategy registry.

Supported strategy sources:

```text
Nautilus Builder-native strategies
Existing Nautilus-Daedalus strategies
Raw NautilusTrader Python strategies
```

Rules:

```text
UX reads strategy metadata through API.
Backend owns discovery/scanning/import.
Existing Daedalus strategies are read-only catalog entries by default.
Compatible existing strategies may be imported/forked as new Draft StrategySpec versions.
UX must not directly scan repos, import Python runtime modules, or edit live strategy files.
```

Safe workflow:

```text
Existing strategy
  → backend catalog entry
  → UX read-only display
  → import/fork as Draft
  → validate
  → backtest
  → Beta/shadow
  → Final
```

Detailed design is defined in:

```text
nautilus_strategy_lab_existing_strategy_registry.md
```

## 22. Product Naming

The product is now named:

```text
Nautilus Builder
```

`Nautilus Strategy Lab` is deprecated as a product name because the scope is broader than strategies.

Product taxonomy:

```text
Nautilus Builder
  ├── Strategy Builder
  ├── AI Builder
  ├── Backtest Lab
  ├── Data & Adapter Manager
  ├── Existing Strategy Registry
  ├── Runtime Console
  ├── Promotion Manager
  └── Release Lifecycle
```

Detailed naming guidance is defined in:

```text
nautilus_builder_naming_architecture.md
```
