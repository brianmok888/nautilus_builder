# Nautilus Builder — Directory Architecture

## 1. Core Decision

All UX code should live in a dedicated frontend application directory.

Recommended:

```text
apps/web/
```

This includes:

- visual strategy builder UI;
- strategy list/detail pages;
- strategy version timeline;
- AI copilot panels;
- adapter/instrument selectors;
- backtest result dashboard;
- terminal/job console;
- promotion/release UI.

However, actual strategy definitions, validation logic, compiler logic, and Nautilus runtime code must not live inside the UX directory.

The frontend edits and displays strategy artifacts. It does not own strategy truth.

---

## 2. Boundary Rule

```text
apps/web = user interface
packages/strategy_spec = strategy contract/truth model
packages/strategy_validation = hard-rule validation
packages/strategy_compiler = safe compiler
services/workers = Nautilus runtime/backtest execution
services/api = backend authority/API
```

The UX may contain view models and form state, but canonical StrategySpec lives in backend/domain packages and database versions.

---

## 3. Recommended Monorepo Layout

```text
repo/
  apps/
    web/
      app/
        strategies/
          page.tsx
          [strategyId]/
            page.tsx
            versions/
              page.tsx
            backtests/
              page.tsx
            promotions/
              page.tsx

        backtests/
          page.tsx
          [jobId]/
            page.tsx

        datasets/
          page.tsx

        adapters/
          page.tsx

        settings/
          page.tsx

      components/
        strategy-builder/
          StrategyBuilderCanvas.tsx
          BlockPalette.tsx
          BlockInspector.tsx
          StrategySpecPreview.tsx
          StrategyStageBadge.tsx
          VersionTimeline.tsx
          PromotionPanel.tsx

        ai-builder/
          AiStrategyCopilot.tsx
          AiRevisionPanel.tsx
          AiExplanationPanel.tsx

        market-config/
          AdapterSelector.tsx
          InstrumentSelector.tsx
          DataTypeSelector.tsx
          TimeframeSelector.tsx
          DateRangePicker.tsx
          DataAvailabilityPanel.tsx

        backtests/
          BacktestRunPanel.tsx
          BacktestStatusCard.tsx
          EquityCurve.tsx
          DrawdownChart.tsx
          TradesTable.tsx
          FillsTable.tsx
          BacktestMetrics.tsx

        terminal/
          JobTerminal.tsx
          TerminalCommandHelp.tsx

        layout/
          Sidebar.tsx
          Header.tsx

      lib/
        api/
          strategies.ts
          backtests.ts
          adapters.ts
          instruments.ts
          promotions.ts
          runtimeEvents.ts

        client-state/
          strategyBuilderStore.ts
          terminalStore.ts

        mappers/
          reactFlowToStrategySpec.ts
          strategySpecToReactFlow.ts

        schemas/
          generatedStrategySpecTypes.ts

      tests/
        strategy-builder/
        backtests/
        terminal/
        lifecycle/

  services/
    api/
      routes/
        strategies.py
        strategy_versions.py
        backtests.py
        adapters.py
        instruments.py
        promotions.py
        runtime_events.py

    workers/
      nautilus_backtest_worker.py
      result_normalizer_worker.py
      shadow_signal_worker.py

  packages/
    strategy_spec/
      models.py
      schema.py
      strategy_spec.schema.json
      examples/

    strategy_validation/
      validator.py
      policies.py
      allowed_blocks.yaml
      forbidden_blocks.yaml
      report.py

    strategy_compiler/
      compiler.py
      graph.py
      hash.py
      artifacts.py

    nautilus_rule_graph/
      config.py
      strategy.py

    adapter_registry/
      models.py
      registry.yaml
      service.py

    lifecycle/
      models.py
      state_machine.py
      versioning.py
      promotion_policy.py

    runtime_events/
      publisher.py
      replay.py

    jobs/
      models.py
      state_machine.py

  skills/
    nt-ai-strategy-builder/
      SKILL.md
      templates/
      rules/

  infra/
    docker-compose.yml
    migrations/
```

---

## 4. Strategy UX vs Strategy Truth

The visual strategy builder has its own frontend state:

```text
React Flow nodes/edges
form values
selected block
unsaved UI draft
panel layout
```

But this is only editor state.

Canonical truth:

```text
StrategySpec
StrategySpecVersion
ValidationReport
CompileArtifact
BacktestResult
PromotionRequest
```

StrategySpec must be generated from UI state and validated by backend before it becomes a persisted version.

---

## 5. Should Strategies Have UX Directories?

Yes, the strategy-related UX should have dedicated UI directories.

Example:

```text
apps/web/components/strategy-builder/
apps/web/app/strategies/
```

But do not put domain strategy runtime here.

Correct:

```text
apps/web/components/strategy-builder/StrategyBuilderCanvas.tsx
packages/strategy_spec/models.py
packages/strategy_compiler/compiler.py
services/workers/nautilus_backtest_worker.py
```

Incorrect:

```text
apps/web/strategies/live_strategy.py
apps/web/strategies/submit_order.ts
apps/web/components/strategy-builder/validator_truth.ts
```

Frontend validators may exist for user convenience, but backend validators remain authoritative.

---

## 6. Frontend Strategy Directory Structure

Recommended:

```text
apps/web/app/strategies/
  page.tsx                         # strategy library/list
  new/
    page.tsx                       # create strategy
  [strategyId]/
    page.tsx                       # overview
    builder/
      page.tsx                     # visual builder
    spec/
      page.tsx                     # StrategySpec editor
    versions/
      page.tsx                     # version history
    versions/[versionId]/
      page.tsx                     # immutable version snapshot
    backtests/
      page.tsx                     # runs for this strategy
    backtests/[jobId]/
      page.tsx                     # result detail
    promotions/
      page.tsx                     # stage/promotion history
```

Component grouping:

```text
apps/web/components/strategy-builder/
apps/web/components/strategy-versioning/
apps/web/components/strategy-validation/
apps/web/components/strategy-promotion/
```

---

## 7. Backend Strategy Directory Structure

Recommended:

```text
services/api/routes/strategies.py
services/api/routes/strategy_versions.py
services/api/routes/promotions.py

packages/strategy_spec/
packages/strategy_validation/
packages/strategy_compiler/
packages/lifecycle/
```

Backend owns:

- schema;
- validation;
- versioning;
- promotion;
- compiler;
- runtime job creation;
- result persistence.

---

## 8. Runtime Strategy Directory Structure

Recommended:

```text
packages/nautilus_rule_graph/
  config.py
  strategy.py
  signal_strategy.py
  backtest_strategy.py

services/workers/
  nautilus_backtest_worker.py
  shadow_signal_worker.py
```

Runtime strategy code must not depend on React or frontend state.

It receives immutable backend artifacts only:

```text
StrategySpecVersion
CompileArtifact
BacktestProfile
AdapterProfile
InstrumentSnapshot
```

---

## 9. UX Must Not Block Backend Runtime

Directory structure should reinforce this:

```text
apps/web
  no long-running jobs
  no runtime ownership
  no direct worker process
  no direct Nautilus execution

services/workers
  owns backtest runtime
  owns long-running process
  owns result generation
```

Frontend calls:

```text
POST /backtests
GET /backtests/{job_id}
GET /runtime-events/{job_id}
POST /backtests/{job_id}/cancel-request
```

Frontend never does:

```text
run_backtest()
start_nautilus_engine()
submit_order()
kill_worker_process()
```

---

## 10. Rule of Thumb

If code answers “what does the user see or click?” it belongs in:

```text
apps/web
```

If code answers “is this strategy valid?” it belongs in:

```text
packages/strategy_validation
```

If code answers “what does this strategy mean?” it belongs in:

```text
packages/strategy_spec
```

If code answers “how does this become a Nautilus strategy?” it belongs in:

```text
packages/strategy_compiler
```

If code answers “how does Nautilus run it?” it belongs in:

```text
services/workers
packages/nautilus_rule_graph
```

If code answers “can this move from Draft to Testing/Beta/Final?” it belongs in:

```text
packages/lifecycle
```

## 11. Repository Dependency Boundary

Directory architecture assumes `nautilus-builder` is a separate repo from official NautilusTrader.

Recommended repo layout:

```text
~/projects/
  nautilus_trader/              # optional upstream clone/reference only
  Nautilus-Daedalus/            # live trading system
  nautilus-builder/        # UX/backtest/lifecycle product
  nautilus-trader-dev-skill/    # AI agent guardrails
```

`nautilus-builder` should install NautilusTrader as a pinned dependency:

```text
nautilus_trader==<pinned-version>
```

It should not contain a vendored `nautilus_trader/` directory.

## 12. Existing Strategy Registry Directories

Add backend-owned registry package:

```text
packages/strategy_registry/
  models.py
  strategy_manifest.py
  daedalus_strategy_scanner.py
  nautilus_strategy_scanner.py
  strategy_catalog.py
  import_to_strategy_spec.py
  safety_classifier.py
```

Add API route:

```text
services/api/routes/external_strategies.py
```

Add UX strategy library components:

```text
apps/web/components/strategy-library/
  StrategyCatalog.tsx
  ExternalStrategyCard.tsx
  ImportAsDraftButton.tsx
  SourceBadge.tsx
  RuntimeBoundaryBadge.tsx
```

Directory boundary:

```text
apps/web displays catalog entries.
packages/strategy_registry owns scanning/import rules.
services/api exposes registry APIs.
apps/web never scans local repos directly.
```

## 13. Nautilus Builder Directory Naming

The repo root should be:

```text
nautilus-builder/
```

Recommended layout remains:

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

The product is broader than strategy authoring, but strategy-specific packages should keep precise names.
