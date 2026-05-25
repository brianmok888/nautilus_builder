# Nautilus Builder — Implementation Plan

## 0. Core Rule

The UX must never be a blocker or owner of backend runtime.

Implementation must follow:

```text
Frontend request creates durable backend state.
Backend queue/worker owns long-running work.
Frontend observes and requests control actions.
Backend continues if frontend disappears.
```

---

## Phase 1 — Foundations

### Goals

Create the minimum backend contracts and project structure.

### Deliverables

```text
apps/web/
  Next.js frontend

services/api/
  FastAPI API gateway

services/workers/
  Nautilus backtest workers

packages/strategy_spec/
  StrategySpec schema and models

packages/strategy_validation/
  validators and policy checks

packages/strategy_compiler/
  compiler to RuleGraphStrategy

infra/
  docker-compose.yml
  postgres
  redis
  object-storage placeholder
```

### Backend Tasks

1. Create `StrategySpec` Pydantic model.
2. Create JSON Schema export.
3. Create `AdapterRegistry` model.
4. Create `InstrumentRegistry` interface.
5. Create database tables:
   - strategy specs;
   - strategy versions;
   - backtest jobs;
   - backtest results;
   - runtime events.
6. Add migration framework.
7. Add idempotent job creation API.

### UX Tasks

1. Create app shell.
2. Add strategy list page.
3. Add strategy detail page.
4. Add basic YAML/JSON StrategySpec editor using Monaco.
5. Add validation result panel.

### Runtime Tasks

1. Add Redis Streams event publisher.
2. Add backend event replay endpoint.
3. Add WebSocket/SSE event stream.
4. Ensure browser disconnect does not cancel backend state.

### Acceptance Criteria

- StrategySpec can be saved and versioned.
- Validator can be called from API.
- BacktestJob can be created and stored.
- Worker can pick up dummy job.
- Runtime events persist independently of UX session.

---

## Phase 2 — StrategySpec and Validators

### Goals

Make user/AI generated specs safe.

### Deliverables

```text
strategy_spec.schema.json
allowed_blocks.yaml
forbidden_blocks.yaml
risk_policy.yaml
validator_report.md
```

### Required Validators

1. Schema validator.
2. Allowed indicator validator.
3. Allowed operator validator.
4. Forbidden execution block validator.
5. Raw-code ban validator.
6. No-lookahead field validator.
7. Bar-close-only validator.
8. Risk block required validator.
9. Parameter bound validator.
10. Adapter/instrument registry validator.

### Forbidden Tokens/Actions

Reject any user/AI spec containing:

```text
submit_order
modify_order
cancel_order
close_position
set_leverage
place_order
broker
exchange_credentials
api_key
secret_key
eval
exec
import
open(
socket
requests
subprocess
os.system
```

### Acceptance Criteria

- Unsafe specs are rejected before compilation.
- Missing exit/risk rules are rejected or downgraded to draft-only.
- Unknown adapters/instruments are rejected.
- Validation report is stored with line/item-level explanations.

---

## Phase 3 — Adapter and Instrument UX

### Goals

Let users configure approved data source adapter and instruments.

### UX Components

```text
AdapterSelector
MarketTypeSelector
VenueSelector
InstrumentSearch
DataTypeSelector
TimeframeSelector
DateRangePicker
DataAvailabilityPanel
SimulationConfigPanel
```

### Backend Components

```text
GET /adapters
GET /adapters/{adapter_id}
GET /instruments?adapter_id=&query=
GET /data-availability?instrument_id=&bar_type=
POST /backtest-profiles/validate
```

### Registry Rules

The UX only displays backend-approved options.

The backend must validate again on submit.

Never trust frontend-selected values without backend registry checks.

### Acceptance Criteria

- User can select approved adapter.
- User can search instruments.
- User can choose bar/tick/L2 data if available.
- UX shows missing data warnings before job start.
- Backend rejects stale or invalid adapter/instrument selections.

---

## Phase 4 — Visual Strategy Builder MVP

### Goals

Build no-code strategy creation using blocks.

### Frontend Stack

```text
React Flow
shadcn/ui
Zustand
TanStack Query
Monaco preview
```

### Blocks v1

Indicators:

```text
EMA
SMA
RSI
MACD
ATR
BollingerBands
VWAP
```

Operators:

```text
crossed_above
crossed_below
gt
lt
gte
lte
and
or
not
```

Risk:

```text
fixed_position_pct
max_position_pct
stop_loss_pct
take_profit_pct
max_hold_bars
```

Outputs:

```text
BacktestSignalObservation
StrategySignalPreview
```

### Compiler UX

Visual graph must serialize to `StrategySpec`.

The canonical source is always `StrategySpec`, not React Flow state.

React Flow state is a view/editor projection.

### Acceptance Criteria

- User can create EMA/RSI strategy visually.
- Visual graph serializes to valid StrategySpec.
- StrategySpec can be loaded back into graph.
- Invalid graph shows inline validation errors.
- No execution block can be added in v1.

---

## Phase 5 — RuleGraphStrategy Compiler

### Goals

Compile safe `StrategySpec` into Nautilus-compatible backtest strategy.

### Design

Use one generic strategy class:

```text
RuleGraphBacktestStrategy
```

It receives a validated spec and evaluates indicators/rules during Nautilus backtest.

For live/shadow Daedalus:

```text
RuleGraphSignalStrategy
```

It emits `StrategySignalPreview` only.

### Compiler Responsibilities

1. Load validated StrategySpec.
2. Build indicator registry.
3. Build rule graph.
4. Resolve input dependencies.
5. Validate time alignment.
6. Generate config for generic Nautilus strategy.
7. Store compile artifact.

### No Codegen v1

Avoid raw Python generation in v1.

Prefer interpreted safe rule graph.

### Acceptance Criteria

- Valid spec compiles to RuleGraphBacktestStrategy config.
- Compiler rejects unknown/unsafe blocks.
- Compiler output is deterministic.
- Same spec/version produces same compile hash.

---

## Phase 6 — Nautilus Backtest Worker

### Goals

Run actual NautilusTrader backtests asynchronously.

### Worker Flow

```text
Load BacktestJob
  → load StrategySpec version
  → load AdapterProfile
  → load Instrument
  → load historical data
  → build Nautilus backtest config
  → attach RuleGraphBacktestStrategy
  → run BacktestEngine/BacktestNode
  → collect orders/fills/positions/trades/equity
  → normalize results
  → store artifacts
  → publish events
```

### Worker Rules

- Worker owns the process, not UX.
- Worker must checkpoint job state.
- Worker must emit progress events.
- Worker must handle cancellation requests through backend state.
- Worker must not read frontend session state.
- Worker must not expose shell access to users.

### Acceptance Criteria

- Backtest starts from API-created job.
- Refreshing browser does not interrupt job.
- Worker restart marks stale running jobs appropriately.
- Result artifacts are persisted.
- Logs are replayable after job completion.

---

## Phase 7 — Results Dashboard

### Views

1. Summary metrics:
   - net PnL;
   - max drawdown;
   - Sharpe;
   - Sortino;
   - win rate;
   - profit factor;
   - exposure;
   - number of trades.
2. Equity curve.
3. Drawdown curve.
4. Candlestick chart with entry/exit markers.
5. Trades table.
6. Fills/orders table.
7. Validation report.
8. Terminal/log panel.
9. Strategy config snapshot.

### Acceptance Criteria

- User can inspect result without rerunning backtest.
- Metrics are generated by backend normalizer.
- StrategySpec version is linked to result.
- Logs and result artifacts are downloadable.

---

## Phase 8 — Live Terminal / Job Console

### Goal

Add terminal-like transparency without making UX a runtime dependency.

### Normal User Mode

Terminal shows:

```text
validation output
compile logs
backtest progress
worker logs
result export logs
warnings/errors
```

Allowed commands:

```text
help
status
show validation
show config
show metrics
tail logs
request cancel
```

No raw shell.

### Admin Mode

Optional later:

```text
sandbox shell
disposable container
no production secrets
audited commands
time-limited session
```

### Acceptance Criteria

- Terminal disconnect does not stop job.
- Terminal reconnect loads prior logs.
- User cannot execute arbitrary backend shell commands.
- Cancel command writes cancellation request to backend state.

---

## Phase 9 — AI Strategy Builder Skill Integration

### Goals

Connect AI copilot to `nautilus-trader-dev-skill`.

### New Skill

```text
skills/nt-ai-strategy-builder/SKILL.md
```

### AI Responsibilities

- convert user intent to StrategySpec draft;
- explain every rule;
- include risk assumptions;
- mark strategy as draft;
- recommend validation/backtest;
- analyze results after backtest.

### AI Restrictions

- no direct live execution code;
- no arbitrary Python;
- no broker credentials;
- no `submit_order`;
- no live promotion;
- no hidden assumptions.

### Acceptance Criteria

- AI output passes through validator before save.
- AI can revise failed specs using validation report.
- AI explains risk and strategy logic.
- AI never becomes a runtime authority.

---

## Phase 10 — Daedalus Shadow Promotion

### Goals

Allow successful backtested strategies to become shadow signal candidates.

### Flow

```text
BacktestResult
  → promotion request
  → validator replay checks
  → shadow readiness report
  → RuleGraphSignalStrategy
  → StrategySignalPreview
  → Redis/MessageBus visibility
  → gate observation
```

### Hard Boundary

Shadow/live profile may not submit simulated or live orders.

It emits only:

```text
StrategySignalPreview
candidate trace metadata
risk hints
confidence metadata
```

### Acceptance Criteria

- Promoted strategy emits `StrategySignalPreview`.
- No `TradeAction` is produced by strategy builder.
- `run_gate_engine` remains sole gate authority.
- `run_execution_lane` remains sole order authority.

---

## Phase 11 — Production Hardening

### Areas

1. Auth and RBAC.
2. Quotas and rate limits.
3. Worker isolation.
4. Job timeout.
5. Artifact retention.
6. Strategy version immutability.
7. Audit logs.
8. Data lineage.
9. Deterministic replay.
10. CI test suite.
11. Security scanning.
12. Disaster recovery.

### Acceptance Criteria

- Every backtest result links to exact spec version, data version, adapter profile, compiler version, and worker image.
- Jobs are reproducible.
- Unsafe specs cannot reach worker execution.
- UI outages do not affect backend jobs or live runtime.

---

## Suggested Milestones

### MVP-1

```text
Spec editor
validator
adapter selector
simple backtest worker
result summary
job console
```

### MVP-2

```text
React Flow visual builder
indicator block library
candlestick result chart
trade markers
StrategySpec versioning
```

### MVP-3

```text
AI strategy builder skill
parameter sweep
result comparison
shadow promotion request
```

### MVP-4

```text
Daedalus signal-preview integration
gate observation dashboard
production candidate workflow
```

## Phase 12 — Lifecycle and Versioning

### Goals

Implement dev-style lifecycle:

```text
Draft → Testing → Beta → Final
```

### Tasks

1. Add stage/version fields to StrategySpecVersion.
2. Add immutable version snapshots.
3. Add promotion request model.
4. Add stage transition validator.
5. Add lifecycle badges in UX.
6. Add promotion buttons based on eligibility.
7. Add tests for immutability and evidence requirements.
8. Add AI rule: all AI-generated strategies start as Draft.
9. Add Final rule: final strategy remains gate/execution-lane bound.

### Required Tests

```text
test_ai_strategy_starts_as_draft
test_draft_version_editable
test_backtested_version_frozen
test_beta_version_frozen
test_final_version_frozen
test_testing_requires_validation
test_beta_requires_backtest_result
test_final_requires_beta_evidence
test_final_cannot_submit_order_directly
```

### Acceptance Criteria

- Every strategy version has lifecycle stage and semver.
- Tested versions cannot be edited in place.
- Promotion requires backend evidence.
- Final release is immutable.
- Final release still cannot bypass Daedalus gate or execution lane.

## Phase 14 — Repository and Dependency Setup

### Goal

Establish clean repo/dependency direction.

### Required Repos

```text
Nautilus-Daedalus
nautilus-builder
nautilus-trader-dev-skill
```

Upstream dependency:

```text
nautilus_trader
```

### Tasks

1. Create/confirm separate `nautilus-builder` repo.
2. Add `nautilus_trader` as pinned dependency.
3. Confirm Nautilus-Daedalus also pins the same `nautilus_trader` version.
4. Add lockfiles.
5. Add compatibility check command.
6. Add shared contract package or artifact schema for Nautilus Builder → Daedalus promotion.
7. Ensure Nautilus Builder can run backtests without booting Daedalus.
8. Ensure Daedalus can consume approved StrategySpec/CompileArtifact through explicit contract.
9. Add CI checks for dependency/version drift.

### Required Tests

```text
test_strategy_lab_imports_nautilus_trader
test_daedalus_imports_nautilus_trader
test_same_nautilus_version_pinned
test_strategy_lab_does_not_import_daedalus_execution_lane
test_strategy_lab_can_run_backtest_worker_without_daedalus_runtime
test_daedalus_can_consume_strategy_spec_contract
```

### Acceptance Criteria

- NautilusTrader is a pinned dependency, not vendored.
- Daedalus depends on NautilusTrader.
- Nautilus Builder depends on NautilusTrader.
- Nautilus Builder and Daedalus do not live inside the official NautilusTrader repo.
- Nautilus Builder integrates with Daedalus through contracts/events/API only.

## Phase 15 — Existing Strategy Registry

### Goal

Allow the UX to read existing strategies safely through backend registry APIs.

### Tasks

1. Add `packages/strategy_registry`.
2. Add backend scanner for Nautilus Builder-native strategies.
3. Add backend scanner for local Nautilus-Daedalus strategy manifests.
4. Add optional raw NautilusTrader strategy metadata scanner.
5. Add `strategy_manifest.yaml` convention.
6. Add Strategy Catalog API routes.
7. Add UX Strategy Library sections:
   - My Strategies
   - Imported Drafts
   - Daedalus Catalog
   - External Nautilus Strategies
   - Final Releases
8. Add import/fork-as-draft flow.
9. Add allowlist/denylist checks for local Daedalus repo scanning.
10. Add tests proving UX cannot edit runtime source directly.

### Required API

```text
GET  /strategies
GET  /strategies/{strategy_id}
GET  /strategies/{strategy_id}/versions
GET  /external-strategies
GET  /external-strategies/daedalus
GET  /external-strategies/nautilus
POST /external-strategies/{external_id}/import-as-draft
POST /external-strategies/{external_id}/fork-as-draft
```

### Required Tests

```text
test_strategy_registry_lists_native_strategy_specs
test_strategy_registry_lists_daedalus_catalog_read_only
test_strategy_registry_imports_compatible_strategy_as_draft
test_imported_strategy_defaults_unvalidated
test_imported_strategy_defaults_not_backtested
test_ux_cannot_edit_daedalus_source_file
test_scanner_does_not_import_execution_lane
test_scanner_respects_denylist
test_raw_nautilus_strategy_read_only_by_default
```

### Acceptance Criteria

- UX can read existing strategies through API.
- Existing Daedalus strategies are read-only by default.
- Compatible strategies can be imported/forked as Draft.
- No live/runtime strategy file is edited in place.
- No registry path can call `submit_order`.

## Phase 16 — Product Rename to Nautilus Builder

### Goal

Rename product references from `Nautilus Strategy Lab` to `Nautilus Builder`.

### Tasks

1. Rename repo target from `nautilus-strategy-lab` to `nautilus-builder`.
2. Rename docs from `nautilus_strategy_lab_*` to `nautilus_builder_*`.
3. Update README/product references.
4. Keep internal package names specific:
   - `strategy_spec`
   - `strategy_validation`
   - `strategy_compiler`
   - `strategy_registry`
5. Rename UI navigation to:
   - Strategy Builder
   - AI Builder
   - Backtest Lab
   - Data & Adapters
   - Strategy Registry
   - Runtime Console
   - Promotions
   - Releases
6. Add migration note: `Nautilus Strategy Lab` is deprecated alias.

### Acceptance Criteria

- No user-facing product reference uses `Nautilus Strategy Lab`.
- Repo/docs use `Nautilus Builder`.
- Strategy-specific module remains named `Strategy Builder`.
- Backtest module is named `Backtest Lab`.
- Existing strategy module is named `Existing Strategy Registry`.
