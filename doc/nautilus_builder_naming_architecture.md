# Nautilus Builder — Naming, Scope, and Product Taxonomy

## 1. Rename Decision

The product name is now:

```text
Nautilus Builder
```

Old name:

```text
Nautilus Strategy Lab
```

Status of old name:

```text
Deprecated alias
```

Reason:

The scope is broader than strategy authoring. It now includes UX, AI assistance, adapter/instrument configuration, data availability, backtesting, existing strategy registry, lifecycle/versioning, terminal/job console, Daedalus promotion, and release management.

---

## 2. Recommended Repository Name

Use:

```text
nautilus-builder
```

Optional full GitHub path:

```text
github.com/brianmok888/nautilus-builder
```

Avoid:

```text
nautilus-strategy-lab
```

because it implies the product is strategy-only.

---

## 3. Product Modules

Nautilus Builder is the top-level product.

Recommended module taxonomy:

```text
Nautilus Builder
  ├── Strategy Builder
  ├── AI Builder
  ├── Backtest Lab
  ├── Data & Adapter Manager
  ├── Instrument Manager
  ├── Existing Strategy Registry
  ├── Runtime Console
  ├── Result Dashboard
  ├── Promotion Manager
  └── Release Lifecycle
```

---

## 4. Naming Rules

Use **Nautilus Builder** when referring to the overall product.

Use **Strategy Builder** when referring specifically to the no-code/AI strategy authoring surface.

Use **Backtest Lab** when referring to NautilusTrader-backed backtest execution and result analysis.

Use **Data & Adapter Manager** when referring to adapter, venue, instrument, data type, timeframe, and data availability configuration.

Use **Existing Strategy Registry** when referring to reading/importing existing Daedalus or raw Nautilus strategies.

Use **Promotion Manager** when referring to Draft → Testing → Beta → Final stage movement.

Use **Runtime Console** when referring to terminal/job logs.

---

## 5. Dependency Naming

The repo/dependency architecture becomes:

```text
official nautilus_trader package
      ↑                  ↑
      │                  │
Nautilus-Daedalus   Nautilus Builder
      ↑                  │
      └── contracts/events/API ──┘
```

Meaning:

```text
NautilusTrader = upstream engine
Nautilus-Daedalus = live signal/gate/execution system
Nautilus Builder = UX/backtest/builder product
nautilus-trader-dev-skill = coding-agent guardrail repo
```

---

## 6. Directory Naming

Recommended root:

```text
nautilus-builder/
```

Internal layout:

```text
nautilus-builder/
  apps/web/
  services/api/
  services/workers/
  packages/strategy_spec/
  packages/strategy_validation/
  packages/strategy_compiler/
  packages/strategy_registry/
  packages/adapter_registry/
  packages/lifecycle/
  packages/runtime_events/
  packages/jobs/
  infra/
```

Keep domain package names specific. Do not rename `strategy_spec` to something vague; it still represents strategy contracts.

---

## 7. UX Naming

UX pages:

```text
/strategies
/strategies/[strategyId]/builder
/backtests
/data
/adapters
/instruments
/registry
/promotions
/runtime-console
/settings
```

Navigation labels:

```text
Strategy Builder
AI Builder
Backtest Lab
Data & Adapters
Strategy Registry
Runtime Console
Promotions
Releases
```

---

## 8. Lifecycle Naming

The staged builder lifecycle remains:

```text
Draft → Testing → Beta → Final
```

This lifecycle applies to strategy artifacts inside Nautilus Builder.

Important:

```text
Final does not mean direct live trading.
Final means frozen approved artifact eligible for controlled Daedalus flow.
```

---

## 9. Documentation Rename Map

Old file names:

```text
nautilus_strategy_lab_spec.md
nautilus_strategy_lab_implementation_plan.md
nautilus_strategy_lab_hardguards.md
nautilus_strategy_lab_implementation_prompts.md
nautilus_strategy_lab_directory_architecture.md
nautilus_strategy_lab_lifecycle_versioning.md
nautilus_strategy_lab_repo_dependency_architecture.md
nautilus_strategy_lab_existing_strategy_registry.md
```

New file names:

```text
nautilus_builder_spec.md
nautilus_builder_implementation_plan.md
nautilus_builder_hardguards.md
nautilus_builder_implementation_prompts.md
nautilus_builder_directory_architecture.md
nautilus_builder_lifecycle_versioning.md
nautilus_builder_repo_dependency_architecture.md
nautilus_builder_existing_strategy_registry.md
nautilus_builder_naming_architecture.md
```

---

## 10. Final Naming Rule

Use this language:

```text
Nautilus Builder is the product.
Strategy Builder is one module.
NautilusTrader is the engine.
Nautilus-Daedalus is the live trading control system.
```
