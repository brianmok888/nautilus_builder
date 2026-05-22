# Nautilus Builder — Repository & Dependency Architecture

## 1. Core Decision

Official NautilusTrader should remain an upstream engine dependency.

Do not put Nautilus-Daedalus or Nautilus Builder inside the official NautilusTrader repo.

Recommended dependency direction:

```text
official nautilus_trader package
      ↑                     ↑
      │                     │
Nautilus-Daedalus      Nautilus Builder
      ↑                     │
      └──── contracts/events/API ────┘
```

Meaning:

```text
NautilusTrader = engine dependency
Nautilus-Daedalus = trading system built on NautilusTrader
Nautilus Builder = UX/backtest product built on NautilusTrader
nautilus-trader-dev-skill = AI/coding-agent guardrail repo
```

---

## 2. What Installs What?

### Official NautilusTrader

Installed as a Python dependency:

```bash
pip install -U nautilus_trader
```

For reproducible systems, pin the version:

```toml
dependencies = [
  "nautilus_trader==<pinned-version>"
]
```

or with `uv`:

```bash
uv add "nautilus_trader==<pinned-version>"
```

---

### Nautilus-Daedalus

Nautilus-Daedalus should install NautilusTrader.

It should not be installed into the official NautilusTrader repo.

```text
Nautilus-Daedalus
  → depends on nautilus_trader
  → owns StateBundle / signal / gate / TradeAction / execution lane
  → uses NautilusTrader for adapters, data model, message bus, strategies, execution, backtest/live primitives
```

Example dependency:

```toml
[project]
name = "nautilus-daedalus"

dependencies = [
  "nautilus_trader==<pinned-version>",
  "pydantic>=2",
  "redis>=5"
]
```

---

### Nautilus Builder

Nautilus Builder should also install NautilusTrader directly.

It should not depend on the whole Daedalus runtime just to run backtests.

```text
Nautilus Builder
  → depends on nautilus_trader
  → runs Nautilus backtest workers
  → owns UX / StrategySpec / validator / compiler / lifecycle
  → integrates with Daedalus only for shadow/promotion/live signal workflow
```

Example dependency:

```toml
[project]
name = "nautilus-builder"

dependencies = [
  "nautilus_trader==<same-pinned-version-as-daedalus>",
  "fastapi",
  "pydantic>=2",
  "redis>=5",
  "sqlalchemy"
]
```

---

## 3. Why Both Daedalus and Nautilus Builder Depend on NautilusTrader?

Because they use NautilusTrader differently.

Daedalus uses NautilusTrader for:

```text
market data ingestion
MessageBus
Strategy/Actor runtime
order factory
execution integration
ExecutionReport evidence
live/paper/sim runtime
```

Nautilus Builder uses NautilusTrader for:

```text
BacktestEngine / BacktestNode
historical replay
simulated fills
portfolio accounting
result generation
strategy validation by replay
```

The Nautilus Builder should be able to run historical backtests without booting the full Daedalus live runtime.

---

## 4. Version Pinning Rule

Daedalus and Nautilus Builder should pin the same NautilusTrader version.

Example:

```text
Nautilus-Daedalus      nautilus_trader==1.x.y
Nautilus Builder  nautilus_trader==1.x.y
```

Reason:

```text
same instrument model
same order/fill semantics
same backtest behavior
same adapter behavior
same message/event definitions
less drift between research and live
```

If one repo upgrades NautilusTrader, both should go through compatibility checks.

---

## 5. Repository Layout

Recommended repositories:

```text
github.com/brianmok888/Nautilus-Daedalus
github.com/brianmok888/nautilus-builder
github.com/brianmok888/nautilus-trader-dev-skill
```

External upstream dependency:

```text
github.com/nautechsystems/nautilus_trader
```

Do not fork NautilusTrader unless there is a specific engine patch requirement.

---

## 6. Local Development Layout

Recommended local workspace:

```text
~/projects/
  nautilus_trader/              # optional upstream clone for reference/debug
  Nautilus-Daedalus/            # your trading system
  nautilus-builder/        # UX + backtest product
  nautilus-trader-dev-skill/    # agent skills/rules
```

Normal development should use the pip package.

Optional editable/source install only when:

```text
debugging Nautilus internals
testing unreleased Nautilus fixes
preparing upstream PR
maintaining a temporary fork patch
```

---

## 7. Do Not Nest Repos

Avoid:

```text
nautilus_trader/
  Nautilus-Daedalus/
  apps/web/
  services/api/
```

Avoid:

```text
Nautilus-Daedalus/
  vendor/nautilus_trader/
```

Avoid:

```text
nautilus-builder/
  nautilus_trader/
```

Use package dependencies and clear integration contracts instead.

---

## 8. Integration Between Nautilus Builder and Daedalus

The Nautilus Builder should not import deep Daedalus runtime internals by default.

Preferred integration:

```text
Nautilus Builder
  → exports approved StrategySpec / CompileArtifact / PromotionRequest
  → Daedalus imports or subscribes through explicit contract
  → Daedalus runs shadow signal profile
  → Daedalus emits StrategySignalPreview
```

Integration options:

```text
API endpoint
Git/versioned artifact registry
Postgres shared read model
Redis Streams event
object storage artifact
manual export/import
```

Avoid tight coupling:

```text
Nautilus Builder directly calls run_execution_lane
Nautilus Builder imports live execution internals
Nautilus Builder creates TradeAction
Nautilus Builder submits Nautilus orders
```

---

## 9. Package Boundary

```text
nautilus_trader
  = upstream engine

Nautilus-Daedalus
  = trading runtime and live authority

nautilus-builder
  = UX/backtest/strategy authoring product

nautilus-trader-dev-skill
  = coding-agent behavior and implementation guardrails
```

The dependency direction should stay one-way:

```text
Daedalus depends on NautilusTrader
Nautilus Builder depends on NautilusTrader
Nautilus Builder integrates with Daedalus through contracts
NautilusTrader depends on none of these
```

---

## 10. Upgrade Policy

When upgrading NautilusTrader:

1. Upgrade in a branch.
2. Run Nautilus Builder backtest compatibility suite.
3. Run Daedalus signal/gate/execution-lane tests.
4. Compare replay outputs.
5. Check instrument/order/fill model changes.
6. Check adapter behavior.
7. Update lockfiles.
8. Record compatibility notes.
9. Promote only after review.

Required tests:

```text
test_strategy_lab_backtest_still_reproducible
test_daedalus_signal_preview_still_deterministic
test_gate_engine_contract_unchanged
test_execution_lane_order_factory_still_valid
test_no_submit_order_boundary_violation
```

---

## 11. When to Upstream Something to NautilusTrader

Only upstream generic, engine-friendly components.

Possible upstream candidates:

```text
StrategySpec concept
RuleGraphStrategy example
visual-builder integration docs
safe backtest config examples
test fixtures
docs for external strategy builder workflow
```

Do not upstream:

```text
Next.js UX
AI copilot
Daedalus gate
Telegram integration
user accounts
Postgres app state
Redis job dashboard
Draft/Testing/Beta/Final product lifecycle
```

---

## 12. Final Recommendation

Use this architecture:

```text
official nautilus_trader
  → installed via pip/uv as pinned dependency

Nautilus-Daedalus
  → installs nautilus_trader
  → owns live signal/gate/execution authority

Nautilus Builder
  → installs nautilus_trader
  → owns UX/backtest/strategy lifecycle
  → talks to Daedalus only through explicit contracts

nautilus-trader-dev-skill
  → guides agents implementing all of the above
```

This keeps the engine clean, the product fast to iterate, and the live trading boundary safe.

## 13. Local Daedalus Reference for Existing Strategy Registry

During development, Nautilus Builder may reference a local Nautilus-Daedalus repo to read strategy manifests and contracts.

Example:

```text
DAEDALUS_REPO_PATH=../Nautilus-Daedalus
DAEDALUS_CONTRACT_MODE=local
DAEDALUS_EXECUTION_IMPORTS_ALLOWED=false
```

Allowed local references:

```text
contracts/
schemas/
strategy_manifests/
strategy_shells/
tests/fixtures/
```

Forbidden local references:

```text
runtime/execution/
live/
brokers/
credentials/
secrets/
.env
```

The registry may read metadata and manifests.

It must not import Daedalus execution runtime, create TradeAction, or call `submit_order`.

## 14. Nautilus Builder Repo Name

The product repo should be named:

```text
nautilus-builder
```

Recommended repositories:

```text
github.com/brianmok888/Nautilus-Daedalus
github.com/brianmok888/nautilus-builder
github.com/brianmok888/nautilus-trader-dev-skill
```

Dependency direction remains:

```text
official nautilus_trader
  ↑
  ├── Nautilus-Daedalus
  └── Nautilus Builder
```
