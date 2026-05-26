# Nautilus Builder — Hard Guards, Safety Rules, and Runtime Boundaries

## 1. Prime Directive

The UX must not be a blocker, owner, or dependency of backend runtime.

```text
Browser closed? Backend continues.
WebSocket disconnected? Backend continues.
Frontend redeployed? Backend continues.
Mobile app asleep? Backend continues.
Terminal panel closed? Backend continues.
```

All long-running tasks must be backend-owned and durable.

---

## 2. Authority Boundaries

```text
UX
  = authoring, configuration, observation, explicit user requests

AI
  = advisory drafting, explanation, revision suggestions

Validator
  = hard safety enforcement

Compiler
  = safe StrategySpec translation

NautilusTrader
  = backtest/replay/paper/live engine primitives

Builder runtime profiles
  = explicit authoring, backtest, research, optimizer, paper, or live mode contracts

Builder paper lane
  = simulated execution only; no live broker credentials

Builder live execution lane
  = future/optional only; disabled by default and allowed only after manual activation, server-side credentials, risk gate, reconciliation, and audit
```

No component may submit live orders except an explicitly enabled Builder live execution lane with `runtime_mode=live`, `live_trading_enabled=true`, `execution_authority=true`, `may_submit_order=true`, manual activation, risk profile, reconciliation, and audit. Existing authoring/backtest/research/promotion UI surfaces remain no-live-authority.

---

## 3. UX Runtime Guards

The UX may not:

- hold process lifetime;
- run strategy logic in the browser as source of truth;
- store only in client state;
- own a long-running backtest;
- directly kill worker processes;
- directly mutate running worker memory;
- directly call broker/exchange APIs;
- directly access exchange credentials;
- directly call Nautilus execution APIs;
- directly create `TradeAction`.

The UX may:

- create durable `BacktestJob`;
- request cancellation through API;
- observe persisted runtime events;
- reconnect and replay state;
- edit draft specs;
- display backend-computed results.

---

## 4. Backend Job Guards

Every long-running job must have:

```text
job_id
status
created_by
created_at
updated_at
strategy_spec_version_id
adapter_profile_id
instrument_id
data_range
worker_id
result_artifact_refs
event_stream_id
```

Job status must not depend on frontend connection.

Workers must check backend state for cancellation, not WebSocket state.

---

## 5. Terminal Guards

Normal user terminal is not a shell.

Allowed:

```text
status
help
show config
show validation
show metrics
tail logs
request cancel
```

Forbidden:

```text
ssh
bash
zsh
python REPL
pip install
docker exec
kubectl
systemctl
rm
curl
wget
nc
scp
reading secrets
environment dump
exchange credentials
```

Admin sandbox terminal, if added, must be:

- disabled by default;
- RBAC protected;
- isolated from production secrets;
- logged;
- time-limited;
- containerized;
- non-blocking to backend runtime.

---

## 6. StrategySpec Guards

The AI and visual builder must produce `StrategySpec`, not direct live code.

Forbidden in specs:

```text
submit_order
modify_order
cancel_order
close_position
set_leverage
place_order
broker_order
exchange_order
api_key
secret_key
credential
eval
exec
import
subprocess
socket
requests
open(
os.
sys.
__import__
```

Unknown blocks are rejected.

Unknown fields are rejected unless explicitly allowed by schema versioning.

---

## 7. Allowed Blocks v1

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

Executable operators:

```text
crossed_above
crossed_below
gt
lt
gte
lte
eq
```

Executable combinators:

```text
all
any
```

`all` represents logical AND and `any` represents logical OR in the current executable schema. `not is not part of the executable MVP schema`; add it only with schema, compiler, and validation tests.

Risk blocks:

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

Live/shadow profile may only emit `StrategySignalPreview`.

---

## 8. Data Guards

Reject strategies that use:

- future bars;
- centered indicators that peek forward;
- future-known labels;
- result-derived features;
- post-fill information inside entry logic;
- future funding rates;
- future liquidation events;
- unaligned timestamps;
- incomplete warmup handling;
- mixed timeframes without explicit alignment.

Required:

```text
bar_close_only: true
no_lookahead_required: true
warmup_period_declared: true
time_index_alignment: strict
```

---

## 9. Adapter and Instrument Guards

UX-selected adapter/instrument must be validated by backend registry.

Reject if:

- adapter disabled;
- instrument unknown;
- data unavailable;
- requested data type unsupported;
- date range unavailable;
- market type mismatched;
- venue model missing;
- fee/slippage model missing;
- user not authorized for dataset.

Do not allow arbitrary adapter import paths.

---

## 10. Backtest Guards

Backtest worker must:

- run in isolated worker process/container;
- use immutable StrategySpec version;
- use immutable data version/catalog snapshot where possible;
- store full config snapshot;
- store validation report;
- store compile hash;
- store worker image/version;
- store result artifacts;
- stream logs/events to backend.

Backtest worker must not:

- read frontend state;
- require browser connection;
- expose shell to user;
- access live exchange credentials;
- perform live order submission.

---

## 11. Daedalus Live Guards

For Nautilus-Daedalus live integration:

```text
StrategySpec
  → RuleGraphSignalStrategy
  → StrategySignalPreview
  → run_gate_engine
  → GateDecision
  → run_execution_lane
```

Forbidden:

```text
StrategySpec → TradeAction
StrategySpec → submit_order
AI → GateDecision approval
UX → TradeAction
UX → submit_order
Visual Builder → live broker API
```

Only `run_gate_engine` may approve/reject/reduce/modify.

Only `run_execution_lane` may call `submit_order(...)`.

---

## 12. AI Guards

AI may:

- draft StrategySpec;
- explain logic;
- suggest improvements;
- analyze results;
- produce validation-aware revisions.

AI may not:

- bypass schema validator;
- bypass policy validator;
- generate direct live execution;
- approve itself for live;
- hide or soften failed results;
- invent backtest metrics;
- claim live readiness without evidence;
- access secrets;
- create arbitrary Python for runtime in v1.

AI output status must default to:

```text
draft
unvalidated
not_backtested
not_live_ready
```

until backend evidence exists.

---

## 13. Promotion Guards

No direct promotion from AI/UX to live.

Required promotion ladder:

```text
draft
  → validated
  → backtested
  → reviewed
  → shadow_candidate
  → shadow_running
  → gate_observed
  → production_candidate
  → manually approved deployment
```

Production approval must include:

- validation report;
- backtest report;
- out-of-sample or walk-forward evidence;
- risk review;
- gate compatibility;
- no-lookahead check;
- runtime boundary check;
- manual approval record.

---

## 14. Observability Guards

Every state transition must be logged.

Required event fields:

```text
event_id
job_id
actor_type
actor_id
stage
level
message
timestamp
metadata
```

Never rely on frontend console logs as the audit record.

---

## 15. Failure Guards

On worker crash:

```text
RUNNING → WORKER_LOST
```

On user cancel request:

```text
RUNNING → CANCEL_REQUESTED → CANCELED
```

On frontend disconnect:

```text
No job state change
```

On invalid spec:

```text
VALIDATING → VALIDATION_FAILED
```

On data issue:

```text
QUEUED/RUNNING → DATA_UNAVAILABLE
```

---

## 16. Security Guards

Do not expose:

- API keys;
- exchange secrets;
- internal file paths;
- raw environment variables;
- container host details;
- database credentials;
- Redis credentials;
- worker host shell.

All artifacts must be scoped by user/project authorization.

---

## 17. Test Guards

Required tests:

```text
test_ux_disconnect_does_not_cancel_job
test_forbidden_submit_order_rejected
test_raw_python_rejected
test_unknown_adapter_rejected
test_unknown_instrument_rejected
test_future_data_rejected
test_strategy_spec_version_immutable_after_backtest
test_terminal_cannot_execute_shell
test_live_profile_emits_signal_preview_only
test_no_trade_action_from_strategy_builder
test_only_execution_lane_can_submit_order
```

---

## 18. Definition of Safe MVP

The MVP is safe only when:

1. UX cannot directly execute shell commands.
2. UX cannot directly submit orders.
3. AI cannot bypass validation.
4. StrategySpec cannot contain execution calls.
5. Backtest job survives browser disconnect.
6. Backtest worker runs asynchronously.
7. Results are persisted.
8. Daedalus live profile emits only `StrategySignalPreview`.
9. `TradeAction` remains gate-owned.
10. `submit_order(...)` remains execution-lane-only.

## 19. Lifecycle and Versioning Guards

Lifecycle stages:

```text
Draft → Testing → Beta → Final
```

Hard guards:

```text
Draft:
  editable, not live-ready, AI/default stage

Testing:
  Nautilus backtest only, version frozen once job starts

Beta:
  shadow/signal-preview only, no TradeAction, no submit_order

Final:
  immutable approved release, still cannot bypass gate/execution lane
```

Forbidden:

```text
editing tested versions in place
editing beta versions in place
editing final versions in place
promoting without evidence
AI marking strategy as Final
UX direct promotion to live
Final strategy direct submit_order
```

Required promotion evidence:

```text
Draft → Testing:
  validation passed

Testing → Beta:
  successful backtest and no-lookahead report

Beta → Final:
  shadow/paper evidence, gate compatibility, manual approval
```

## 21. Repository and Dependency Guards

Dependency direction must remain:

```text
nautilus_trader
  ↑
  ├── Nautilus-Daedalus
  └── Nautilus Builder
```

Forbidden:

```text
putting Nautilus Builder UX inside official NautilusTrader repo
putting Daedalus inside official NautilusTrader repo
vendoring NautilusTrader inside Daedalus
vendoring NautilusTrader inside Nautilus Builder
Nautilus Builder importing Daedalus execution lane directly
Nautilus Builder creating TradeAction directly
Nautilus Builder calling submit_order directly
```

Required:

```text
pin same nautilus_trader version in Daedalus and Nautilus Builder
record compatibility matrix
run upgrade tests before changing NautilusTrader version
integrate Nautilus Builder → Daedalus through explicit contracts/events/API
```

Upgrade guard:

```text
No NautilusTrader upgrade is accepted until Nautilus Builder backtest tests and Daedalus signal/gate/execution-lane tests pass.
```

## 22. Existing Strategy Registry Guards

The UX may read existing strategies only through backend APIs.

Allowed:

```text
UX lists catalog entries
UX views strategy metadata
UX imports/forks compatible strategy as Draft
Backend scanner reads manifests/contracts
Backend validates import safety
```

Forbidden:

```text
UX directly scans local repo
UX imports Python strategy modules
UX edits Daedalus runtime source files
UX hot-patches live strategies
UX creates TradeAction from existing strategy
UX calls submit_order
Strategy registry imports run_execution_lane
Strategy registry loads credentials/secrets
```

Backend scanner allowlist:

```text
contracts/
schemas/
strategy_manifests/
strategy_shells/
tests/fixtures/
```

Backend scanner denylist:

```text
runtime/execution/
live/
brokers/
credentials/
secrets/
.env
```

Import/fork guard:

```text
Existing strategy → new Draft StrategySpec
Never edit original source in place
```

## 23. Naming Guards

Use:

```text
Nautilus Builder = top-level product
Strategy Builder = strategy authoring module
Backtest Lab = NautilusTrader-backed backtest module
Data & Adapter Manager = adapter/instrument/data config
Existing Strategy Registry = existing strategy catalog/import module
Runtime Console = terminal/job console
Promotion Manager = lifecycle promotion module
```

Avoid using `Nautilus Strategy Lab` as the product name in new docs, code comments, API labels, or UI text.

Do not rename specific domain packages into vague names. Keep:

```text
strategy_spec
strategy_validation
strategy_compiler
strategy_registry
```

because they describe specific bounded contexts.
