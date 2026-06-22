# Nautilus Builder — Implementation Prompts for Coding Agents

## How to Use These Prompts

Use these prompts with the installed `superpowers:nt` workflow.

Recommended skill chain:

```text
superpowers:nt
  → nt-architect          # component boundaries and NautilusTrader mapping
  → nt-implement          # Strategy/Actor/Indicator/custom component templates
  → nt-strategy-builder   # backtest/live-system assembly when applicable
  → nt-adapters           # only when adapter/provider integration is in scope
  → nt-live               # only for TradingNode/runtime lifecycle work
  → nt-backtest           # backtest engine, fill/matching model, result evidence
  → nt-testing            # DataTester/ExecTester and repo test fixtures
  → nt-review             # final trading, safety, FFI, and deployment review
```

Do not implement everything in one blob.


## 2026-06-22 Prompt Routing Correction

The current installed skill surface does **not** include a standalone
`nt-ai-strategy-builder` skill. AI strategy-builder work must route through the
installed `superpowers:nt` router and the narrower NT skills listed above. Keep
AI output advisory/draft-only until StrategySpec validation, NautilusTrader
backtest evidence, promotion evidence, and `nt-review` all pass.

Each prompt must produce:

1. plan;
2. files to change;
3. tests first or alongside implementation;
4. implementation;
5. verification output;
6. review of boundary rules.

---

# Prompt 1 — Create StrategySpec Schema and Models

```text
Use the installed `superpowers:nt` router.

Task:
Create the StrategySpec schema/model layer for Nautilus Builder.

Context:
Users will create strategies visually or through AI. The output must be a safe, structured StrategySpec, not arbitrary Python. Backend will later compile this spec into a NautilusTrader backtest strategy or Daedalus signal-preview strategy.

Hard rules:
- Do not allow raw Python in v1.
- Do not allow submit_order, modify_order, cancel_order, close_position, set_leverage, or broker/exchange credentials.
- StrategySpec must support adapter_id, venue, instrument_id, bar_type, data range, indicators, rules, risk, and validation flags.
- Live profile must default to signal_preview_only.
- StrategySpec versions must be immutable once used by a BacktestJob.
- UX must not own runtime state.

Required files:
- packages/strategy_spec/models.py
- packages/strategy_spec/schema.py
- packages/strategy_spec/strategy_spec.schema.json
- packages/strategy_spec/examples/ema_rsi_pullback.yaml
- tests/strategy_spec/test_schema_valid.py
- tests/strategy_spec/test_schema_rejects_unknown_fields.py

Implementation requirements:
- Use Pydantic models.
- Export JSON schema.
- Provide strict enum types for indicators/operators/output modes.
- Include schema_version.
- Include status: draft/validated/backtested/shadow_candidate.
- Include created_by: user/ai_builder/imported.

Acceptance tests:
- valid EMA/RSI spec passes;
- unknown indicator fails;
- unknown operator fails;
- arbitrary unknown fields fail;
- live_execution_direct mode fails;
- missing risk block fails or is marked draft-only according to policy.

Deliver:
- summary of implemented files;
- test command;
- test results;
- remaining gaps.
```

---

# Prompt 2 — Build Hard-Rule Validator

```text
Use the installed `superpowers:nt` router.

Task:
Implement the StrategySpec hard-rule validator.

Context:
AI and visual builder outputs are untrusted. The validator is the enforcement layer before compilation or backtesting.

Hard rules:
- Reject execution calls: submit_order, modify_order, cancel_order, close_position, set_leverage, place_order.
- Reject raw code: eval, exec, import, subprocess, socket, requests, open, os, sys, __import__.
- Reject exchange credential references.
- Reject future-looking fields and lookahead operators.
- Require bar_close_only=true for v1.
- Require no_lookahead_required=true.
- Require risk controls: stop loss or explicit exit rule, position sizing, max position cap.
- Validate adapter_id and instrument_id through backend registries.
- UX-selected values are never trusted without backend validation.

Required files:
- packages/strategy_validation/validator.py
- packages/strategy_validation/policies.py
- packages/strategy_validation/allowed_blocks.yaml
- packages/strategy_validation/forbidden_blocks.yaml
- packages/strategy_validation/report.py
- tests/strategy_validation/test_forbidden_execution.py
- tests/strategy_validation/test_forbidden_raw_code.py
- tests/strategy_validation/test_risk_policy.py
- tests/strategy_validation/test_no_lookahead.py
- tests/strategy_validation/test_adapter_registry_validation.py

Acceptance tests:
- spec containing submit_order is rejected;
- spec containing raw Python is rejected;
- missing stop/exit risk is rejected;
- unknown adapter is rejected;
- unknown instrument is rejected;
- valid EMA/RSI spec produces ValidationReport(status=passed).

Deliver:
- implementation summary;
- validation report format;
- test results;
- exact rejected examples.
```

---

# Prompt 3 — Adapter and Instrument Registry

```text
Use the installed `superpowers:nt` router.

Task:
Implement backend-approved AdapterRegistry and InstrumentRegistry APIs.

Context:
UX must allow users to configure data source adapter and instrument, but only through backend-approved registry entries. UX must not accept arbitrary adapter import paths.

Hard rules:
- AdapterRegistry is backend-owned.
- Frontend can display options but backend must revalidate every submitted adapter/instrument.
- Do not allow arbitrary Python class paths.
- Data-only adapters must be marked data-only.
- Backtest profile may use simulated execution.
- Live profile must not create execution authority.

Required files:
- services/api/routes/adapters.py
- services/api/routes/instruments.py
- packages/adapter_registry/models.py
- packages/adapter_registry/registry.yaml
- packages/adapter_registry/service.py
- packages/instrument_registry/service.py
- tests/adapter_registry/test_adapter_registry.py
- tests/adapter_registry/test_instrument_validation.py

API endpoints:
- GET /adapters
- GET /adapters/{adapter_id}
- GET /instruments?adapter_id=&query=
- GET /data-availability?instrument_id=&bar_type=&start=&end=
- POST /backtest-profiles/validate

Acceptance tests:
- enabled adapter appears in GET /adapters;
- disabled adapter cannot be used;
- unknown adapter rejected;
- unknown instrument rejected;
- unsupported data type rejected;
- frontend-provided adapter import path rejected.

Deliver:
- API examples;
- registry example;
- test results.
```

---

# Prompt 4 — Async Backtest Job Runtime

```text
Use the installed `superpowers:nt` router.

Task:
Implement durable asynchronous BacktestJob runtime.

Context:
UX must not block or own backend runtime. Browser disconnect, refresh, or frontend crash must not cancel jobs. Backend worker owns long-running NautilusTrader backtest process.

Hard rules:
- API creates a durable BacktestJob and returns job_id.
- Worker picks up job from queue/state.
- Job progress is stored as RuntimeEvents.
- WebSocket/SSE is observation only.
- Frontend disconnect must not change job state.
- Cancel is explicit: frontend writes cancellation request through API; worker observes state and exits safely.
- No raw shell from terminal.

Required files:
- services/api/routes/backtests.py
- services/api/routes/runtime_events.py
- services/workers/backtest_worker.py
- packages/jobs/models.py
- packages/jobs/state_machine.py
- packages/runtime_events/publisher.py
- packages/runtime_events/replay.py
- tests/jobs/test_job_lifecycle.py
- tests/jobs/test_disconnect_does_not_cancel.py
- tests/jobs/test_cancel_request.py

Job states:
CREATED, VALIDATING, VALIDATED, COMPILING, COMPILED, QUEUED, RUNNING, NORMALIZING_RESULTS, SUCCEEDED, VALIDATION_FAILED, COMPILE_FAILED, DATA_UNAVAILABLE, BACKTEST_FAILED, CANCEL_REQUESTED, CANCELED, WORKER_LOST, TIMEOUT.

Acceptance tests:
- POST /backtests returns job_id quickly;
- worker can run a dummy job after API request completes;
- simulated WebSocket disconnect does not change job status;
- explicit cancel request changes state to CANCEL_REQUESTED then CANCELED;
- runtime events are replayable after reconnect.

Deliver:
- state machine diagram;
- API examples;
- test results.
```

---

# Prompt 5 — RuleGraphStrategy Compiler

```text
Use the installed `superpowers:nt` router.

Task:
Implement StrategySpec compiler to safe RuleGraph strategy configs.

Context:
Valid StrategySpec must compile to a generic NautilusTrader-compatible strategy configuration. Avoid raw Python code generation in v1.

Hard rules:
- Compiler only accepts ValidationReport(status=passed).
- Compiler rejects unknown blocks.
- Compiler output must be deterministic.
- Same spec version must produce same compile hash.
- Backtest profile may produce simulated signal observations inside Nautilus backtest.
- Daedalus live/shadow profile may only emit StrategySignalPreview.
- Compiler must not produce submit_order in live/shadow profile.

Required files:
- packages/strategy_compiler/compiler.py
- packages/strategy_compiler/graph.py
- packages/strategy_compiler/hash.py
- packages/strategy_compiler/artifacts.py
- packages/nautilus_rule_graph/config.py
- packages/nautilus_rule_graph/strategy.py
- tests/strategy_compiler/test_compile_valid_spec.py
- tests/strategy_compiler/test_compile_hash_deterministic.py
- tests/strategy_compiler/test_live_profile_signal_only.py

Acceptance tests:
- valid EMA/RSI spec compiles;
- compile hash stable across runs;
- unknown block fails;
- backtest profile config is produced;
- live profile emits only StrategySignalPreview;
- no TradeAction or submit_order appears in live compiled artifact.

Deliver:
- compiler artifact example;
- test results;
- boundary review.
```

---

# Prompt 6 — NautilusTrader Backtest Worker

```text
Use the installed `superpowers:nt` router.

Task:
Implement the NautilusTrader backtest worker that executes compiled RuleGraph strategies.

Context:
Backend should run NautilusTrader backtests asynchronously from durable BacktestJob state. UX observes progress only.

Hard rules:
- Worker uses immutable StrategySpec version.
- Worker uses approved AdapterProfile and Instrument.
- Worker stores exact config snapshot.
- Worker publishes runtime events.
- Worker persists result artifacts.
- Worker must not require frontend connection.
- Worker must not access live exchange credentials.
- Worker must not expose raw shell.

Required files:
- services/workers/nautilus_backtest_worker.py
- packages/backtest_runner/runner.py
- packages/backtest_runner/config_builder.py
- packages/backtest_runner/result_normalizer.py
- packages/backtest_runner/artifacts.py
- tests/backtest_runner/test_runner_dummy_data.py
- tests/backtest_runner/test_result_normalizer.py
- tests/backtest_runner/test_no_live_credentials.py

Acceptance tests:
- worker runs a minimal backtest using fixture data;
- result includes equity curve, trades, fills/orders if available, summary metrics, logs;
- result links exact StrategySpec version and compile hash;
- no frontend connection needed;
- no live credentials loaded.

Deliver:
- sample BacktestResult JSON;
- artifact list;
- test results.
```

---

# Prompt 7 — Visual Strategy Builder UX

```text
Use the installed `superpowers:nt` router.

Task:
Build the Visual Strategy Builder MVP.

Context:
User should create strategy graph visually. The canonical persisted artifact is StrategySpec, not React Flow state.

Hard rules:
- UX cannot create unsupported blocks.
- UX cannot create execution blocks.
- UX cannot create live direct execution mode.
- UX submits StrategySpec to backend validator.
- UX does not run strategy logic as source of truth.
- UX does not own backend runtime.

Frontend stack:
- Next.js
- React
- TypeScript
- React Flow
- Monaco Editor
- TanStack Query
- Zustand
- shadcn/ui

Required components:
- StrategyBuilderCanvas
- BlockPalette
- BlockInspector
- StrategySpecPreview
- ValidationPanel
- AdapterSelector
- InstrumentSelector
- BacktestRunPanel

Acceptance tests:
- user can create EMA/RSI graph;
- graph serializes to StrategySpec;
- StrategySpec can load back into graph;
- invalid graph shows validation errors;
- forbidden execution blocks are unavailable;
- backend validation errors display inline.

Deliver:
- component list;
- screenshots or storybook stories if available;
- test results.
```

---

# Prompt 8 — Live Terminal / Job Console

```text
Use the installed `superpowers:nt` router.

Task:
Implement a browser terminal-style job console using xterm.js.

Context:
Terminal provides transparency into validation/compile/backtest logs. It must not be a production shell and must not own runtime process lifetime.

Hard rules:
- Normal user terminal is read-only plus approved commands.
- No raw shell.
- No SSH.
- No arbitrary command execution.
- Terminal disconnect does not cancel backend job.
- Reconnect replays previous logs.
- Cancel command must call backend cancel API, not kill process directly.

Allowed commands:
- help
- status
- show config
- show validation
- show metrics
- tail logs
- request cancel

Required files:
- apps/web/components/JobTerminal.tsx
- apps/web/lib/terminalCommands.ts
- services/api/routes/job_terminal.py
- packages/runtime_events/replay.py
- tests/terminal/test_allowed_commands.py
- tests/terminal/test_forbidden_shell.py
- tests/terminal/test_reconnect_replay.py

Acceptance tests:
- terminal shows logs from persisted runtime events;
- forbidden shell command rejected;
- reconnect replays log history;
- terminal close does not cancel job;
- request cancel writes cancellation request through API.

Deliver:
- command spec;
- test results;
- security review.
```

---

# Prompt 9 — AI Strategy Builder Skill

```text
Use the installed `superpowers:nt` router.

Task:
Refresh the AI strategy-builder prompt guidance using the installed `superpowers:nt` skill surface; do not assume a separate `nt-ai-strategy-builder` skill exists.

Context:
AI should help users create safe StrategySpec drafts for Nautilus-backed backtesting and Daedalus signal-preview promotion. AI is advisory only.

Hard rules:
- AI outputs StrategySpec, not live code.
- AI marks output draft/unvalidated/not_backtested.
- AI explains every indicator, rule, and risk assumption.
- AI never calls submit_order or creates TradeAction.
- AI never claims strategy is live-ready without backend evidence.
- AI must revise based on ValidationReport if validation fails.
- Daedalus live profile may emit StrategySignalPreview only.

Required files:
- doc/nautilus_builder_implementation_prompts.md
- docs/superpowers/prompts/2026-05-22-nautilus-builder-implementation-prompts-revised.md
- tests/ai_builder/test_instructor_provider_contract.py
- tests/ai_builder/test_prompt_redaction.py
- tests/web/test_sectioned_operator_ui.py
- update skills/nt/SKILL.md router

Acceptance tests:
- `superpowers:nt` routes AI/UX strategy-builder tasks through nt-architect, nt-implement/nt-strategy-builder, nt-testing, and nt-review;
- skill forbids raw live execution;
- skill requires StrategySpec output;
- skill references validators as enforcement layer;
- prompt guidance routes backtest implementation to nt-strategy-builder/nt-backtest;
- prompt guidance routes final safety review to nt-review.

Deliver:
- new skill files;
- router diff;
- example user prompt and expected AI output;
- review checklist.
```

---

# Prompt 10 — Daedalus Shadow Promotion Integration

```text
Use the installed `superpowers:nt` router.

Task:
Implement shadow promotion path from backtested StrategySpec to Daedalus StrategySignalPreview lane.

Context:
A strategy with acceptable backtest results may be promoted to shadow mode. Shadow mode must not create TradeAction directly and must not submit orders.

Hard rules:
- Promotion requires validation report and backtest result.
- Shadow strategy emits StrategySignalPreview only.
- No submit_order.
- No TradeAction creation.
- run_gate_engine remains sole gate authority.
- run_execution_lane remains sole live order authority.
- Telegram may display signal/gated signal only unless execution reports exist.

Required files:
- packages/promotion/models.py
- packages/promotion/readiness_checker.py
- packages/daedalus_signal_adapter/rule_graph_signal_strategy.py
- services/api/routes/promotions.py
- tests/promotion/test_shadow_readiness.py
- tests/promotion/test_signal_preview_only.py
- tests/promotion/test_no_trade_action.py

Acceptance tests:
- promotion rejected without validation report;
- promotion rejected without backtest result;
- shadow deployment emits StrategySignalPreview;
- no TradeAction can be emitted;
- submit_order is absent;
- gate/execution lane boundaries preserved.

Deliver:
- promotion state machine;
- sample readiness report;
- test results;
- boundary audit.
```

---

# Prompt 11 — End-to-End MVP Verification

```text
Use the installed `superpowers:nt` router.

Task:
Run end-to-end verification for Nautilus Builder MVP.

Scenario:
User creates EMA/RSI strategy using visual builder, selects BINANCE_PERP adapter and BTCUSDT-PERP.BINANCE instrument, validates spec, starts backtest, disconnects/reconnects browser, views results, and requests shadow promotion.

Hard rules to verify:
- UX does not own runtime.
- Browser disconnect does not cancel job.
- AI/UX cannot submit orders.
- StrategySpec cannot contain forbidden execution actions.
- Backtest runs through backend worker.
- Results persist.
- Shadow promotion emits StrategySignalPreview only.
- run_execution_lane remains only submit_order path.

Required tests:
- E2E frontend flow;
- API integration flow;
- worker integration flow;
- validator negative tests;
- reconnect event replay test;
- shadow boundary test.

Deliver:
- full E2E test report;
- failed checks and fixes;
- final safety checklist;
- explicit statement whether MVP is safe for local demo, paper mode, or live candidate.
```

# Prompt 12 — Lifecycle and Versioning

```text
Use the installed `superpowers:nt` router.

Task:
Implement dev-style lifecycle and versioning for Nautilus Builder.

Lifecycle:
Draft → Testing → Beta → Final

Context:
Users and AI create strategies through UX. Strategies must move through controlled stages before becoming final approved releases. Final does not mean direct live execution. Final only means frozen approved candidate eligible for controlled Daedalus flow.

Hard rules:
- AI-generated strategies always start as Draft.
- Draft versions are editable.
- Any version used in a BacktestJob is frozen.
- Beta versions are frozen.
- Final versions are frozen.
- Promotion requires evidence.
- Final cannot bypass run_gate_engine.
- Final cannot bypass run_execution_lane.
- Final cannot call submit_order directly.
- Historical backtest results must link to exact immutable strategy version.

Required files:
- packages/lifecycle/models.py
- packages/lifecycle/state_machine.py
- packages/lifecycle/versioning.py
- packages/lifecycle/promotion_policy.py
- services/api/routes/strategy_versions.py
- services/api/routes/promotions.py
- apps/web/components/StrategyStageBadge.tsx
- apps/web/components/PromotionPanel.tsx
- tests/lifecycle/test_versioning.py
- tests/lifecycle/test_stage_transitions.py
- tests/lifecycle/test_immutability.py
- tests/lifecycle/test_final_no_execution_bypass.py

Version format:
MAJOR.MINOR.PATCH-STAGE.N

Examples:
0.1.0-draft.1
0.2.0-test.1
0.3.0-beta.1
1.0.0

Acceptance tests:
- AI strategy starts as Draft.
- Draft can be edited.
- Backtested version is frozen.
- Beta version is frozen.
- Final version is frozen.
- Testing requires validation report.
- Beta requires successful backtest.
- Final requires beta/shadow evidence and manual approval.
- Final does not generate TradeAction directly.
- Final does not call submit_order.

Deliver:
- lifecycle state machine;
- migration/model changes;
- UX stage badge behavior;
- promotion policy;
- test results;
- boundary audit.
```

# Prompt 14 — Repository and Dependency Setup

```text
Use the installed `superpowers:nt` router.

Task:
Implement clean repository and dependency setup for Nautilus Builder and Nautilus-Daedalus.

Context:
Official NautilusTrader must remain an upstream engine dependency installed via pip/uv. Nautilus-Daedalus and Nautilus Builder should each install the same pinned NautilusTrader version. Neither product should be nested inside the official NautilusTrader repo.

Hard rules:
- Do not vendor NautilusTrader.
- Do not place Nautilus Builder UX inside official NautilusTrader.
- Do not place Daedalus inside official NautilusTrader.
- Nautilus-Daedalus depends on nautilus_trader.
- Nautilus Builder depends on nautilus_trader.
- Nautilus Builder must run backtest workers without booting Daedalus runtime.
- Nautilus Builder may integrate with Daedalus only through explicit contracts/events/API.
- Nautilus Builder must not import run_execution_lane.
- Nautilus Builder must not call submit_order.
- Pin the same NautilusTrader version in both repos.

Required files:
- pyproject.toml
- uv.lock or equivalent lockfile
- docs/repo_dependency_architecture.md
- packages/contracts/strategy_spec_contract.py or equivalent
- tests/dependencies/test_nautilus_version_pinned.py
- tests/dependencies/test_no_vendored_nautilus.py
- tests/dependencies/test_strategy_lab_no_execution_lane_import.py
- tests/dependencies/test_backtest_worker_runs_without_daedalus.py

Acceptance tests:
- both repos import nautilus_trader from package dependency;
- same pinned version is used;
- no vendored nautilus_trader directory exists;
- Nautilus Builder cannot import Daedalus execution lane;
- Nautilus Builder can run a minimal backtest worker without Daedalus runtime;
- Daedalus can consume StrategySpec contract from explicit contract artifact.

Deliver:
- dependency tree;
- pyproject diff;
- lockfile status;
- compatibility test results;
- boundary audit.
```

# Prompt 15 — Existing Strategy Registry and Import

```text
Use the installed `superpowers:nt` router.

Task:
Implement the existing strategy registry and safe import/fork flow.

Context:
UX should be able to read existing strategies from Nautilus Builder, local Nautilus-Daedalus, and optionally raw NautilusTrader strategy modules. The UX must read through backend APIs only. It must not directly scan repos, import Python runtime modules, edit live source files, or touch execution lane code.

Hard rules:
- UX reads strategy metadata through API.
- Backend owns discovery/scanning/import.
- Existing Daedalus strategies are read-only catalog entries by default.
- Compatible existing strategies may be imported/forked as new Draft StrategySpec versions.
- Imported strategies start unvalidated and not backtested.
- Strategy registry must not import run_execution_lane.
- Strategy registry must not call submit_order.
- Scanner must use allowlist/denylist boundaries.
- Raw NautilusTrader Python strategies are read-only unless importer can map safely to StrategySpec.

Required files:
- packages/strategy_registry/models.py
- packages/strategy_registry/strategy_manifest.py
- packages/strategy_registry/daedalus_strategy_scanner.py
- packages/strategy_registry/nautilus_strategy_scanner.py
- packages/strategy_registry/strategy_catalog.py
- packages/strategy_registry/import_to_strategy_spec.py
- packages/strategy_registry/safety_classifier.py
- services/api/routes/external_strategies.py
- apps/web/app/strategies/page.tsx
- apps/web/components/strategy-library/StrategyCatalog.tsx
- apps/web/components/strategy-library/ExternalStrategyCard.tsx
- apps/web/components/strategy-library/ImportAsDraftButton.tsx
- tests/strategy_registry/test_catalog_native.py
- tests/strategy_registry/test_catalog_daedalus_read_only.py
- tests/strategy_registry/test_import_as_draft.py
- tests/strategy_registry/test_scanner_denylist.py
- tests/strategy_registry/test_no_execution_lane_import.py

Required APIs:
- GET /external-strategies
- GET /external-strategies/daedalus
- GET /external-strategies/nautilus
- POST /external-strategies/{external_id}/import-as-draft
- POST /external-strategies/{external_id}/fork-as-draft

Acceptance tests:
- native StrategySpec strategies appear in UX library;
- Daedalus strategies appear as read-only catalog entries;
- compatible Daedalus strategy can import as 0.1.0-draft.1;
- imported strategy is unvalidated/not_backtested/not_live_ready;
- scanner respects denylist;
- no execution lane import exists;
- no submit_order path exists;
- UX cannot edit Daedalus source file directly.

Deliver:
- registry model summary;
- manifest example;
- API examples;
- UX strategy library screenshots or component summary;
- test results;
- boundary audit.
```

# Prompt 16 — Rename Product to Nautilus Builder

```text
Use the installed `superpowers:nt` router.

Task:
Rename the product from Nautilus Strategy Lab to Nautilus Builder.

Context:
The product scope now includes more than strategy building: AI builder, data/adapter manager, instrument manager, backtest lab, runtime console, existing strategy registry, promotion manager, and release lifecycle.

Hard rules:
- User-facing product name must be Nautilus Builder.
- Repo target should be nautilus-builder.
- Strategy authoring module should be called Strategy Builder.
- Backtesting module should be called Backtest Lab.
- Do not rename specific domain packages to vague names.
- Keep packages/strategy_spec, packages/strategy_validation, packages/strategy_compiler, packages/strategy_registry.
- NautilusTrader remains the engine dependency.
- Nautilus-Daedalus remains the live trading control system.

Required updates:
- README.md
- docs/*
- apps/web navigation labels
- app metadata/title
- package/project name where appropriate
- deployment labels
- API OpenAPI title
- tests that check UI/product labels

Acceptance tests:
- grep shows no user-facing `Nautilus Strategy Lab` references except migration/deprecated-alias note;
- UI nav shows Nautilus Builder;
- repo/package metadata uses nautilus-builder;
- Strategy Builder remains as module name;
- domain packages retain specific names.

Deliver:
- rename summary;
- changed files;
- grep verification;
- test results.
```
