# Nautilus Builder — Revised Implementation Prompt Pack

## How to Use This Pack

This prompt pack is the execution layer for building Nautilus Builder through bounded, verifiable seams.

It must be used together with:

- `docs/superpowers/designs/2026-05-22-nautilus-builder-prompt-system-execution-design.md`
- `docs/superpowers/audits/2026-05-22-nautilus-builder-prompt-pack-audit.md`

## Global Scope Rule

- Build inside the Nautilus Builder workspace only.
- Do not touch the Nautilus-Daedalus repository.
- Any Daedalus-related prompt is Builder-side only and may use contracts, payloads, mocks, fixtures, or external-integration assumptions.
- The frontend is an authoring and observation surface only. It must not own runtime truth.

## Dual-Mode Usage

### OpenCode-aware mode

Use the relevant skills, routers, subagents, review loops, and verification workflow available in the host environment.

### Generic-agent mode

Use the same prompts without tool-specific assumptions:

- inspect repository truth first;
- plan before implementation;
- add tests before or alongside changes;
- keep scope bounded;
- run verification commands;
- report changed files, evidence, and remaining gaps.

The two modes must preserve the same scope, safety rules, and acceptance criteria.

## Standard Prompt Metadata

Each prompt declares:

- `Prompt ID`
- `Phase`
- `Depends on`
- `Unlocks`
- `Can run in parallel with`

## Prompt Template Contract

Every prompt below includes:

1. Goal
2. Why this exists
3. Prerequisites
4. Scope included
5. Scope excluded
6. Explicit non-goals
7. Required files to create or change
8. Tests to add first or alongside
9. Implementation constraints
10. Verification commands
11. Expected evidence
12. Boundary/self-review checklist
13. Remaining gaps

## Phase Index

- `FND-01` StrategySpec schema and models
- `SAFE-01` hard-rule validator
- `SAFE-02` adapter and instrument registry
- `RUN-01` async backtest job runtime
- `COMP-01` RuleGraphStrategy compiler
- `COMP-02` NautilusTrader backtest worker
- `UX-01` visual strategy builder UX
- `UX-02` live terminal and job console
- `AI-01` AI strategy builder flow
- `GOV-01` lifecycle and versioning
- `GOV-02` repository and dependency setup
- `GOV-03` existing strategy registry and safe import
- `GOV-04` Builder-side promotion contract
- `SYS-01` end-to-end MVP verification
- `GOV-05` rename product to Nautilus Builder consistency pass

---

## `FND-01` — StrategySpec Schema and Models

- **Phase:** FND
- **Depends on:** none
- **Unlocks:** `SAFE-01`, `SAFE-02`, `RUN-01`, `COMP-01`, `UX-01`, `AI-01`, `GOV-01`
- **Can run in parallel with:** none

### Goal

Create the StrategySpec schema/model layer for Nautilus Builder.

### Why this exists

StrategySpec is the canonical Builder artifact for visual and AI-authored strategies. Later validation, compilation, backtests, lifecycle, and UX all depend on it.

### Prerequisites

- source-doc review of spec, hardguards, and lifecycle docs

### Scope included

- Pydantic models
- JSON Schema export
- strict enums and safe status fields
- example spec artifact

### Scope excluded

- compiler logic
- live execution logic
- runtime worker integration

### Explicit non-goals

- raw Python strategy authoring
- direct order-submission primitives
- frontend-owned truth models

### Required files to create or change

- `packages/strategy_spec/models.py`
- `packages/strategy_spec/schema.py`
- `packages/strategy_spec/strategy_spec.schema.json`
- `packages/strategy_spec/examples/ema_rsi_pullback.yaml`
- `tests/strategy_spec/test_schema_valid.py`
- `tests/strategy_spec/test_schema_rejects_unknown_fields.py`

### Tests to add first or alongside

- valid EMA/RSI spec passes
- unknown indicator fails
- unknown operator fails
- unknown fields fail
- forbidden live execution mode fails

### Implementation constraints

- versions immutable once used by BacktestJob
- include `schema_version`, lifecycle status, and provenance fields
- missing risk block must fail or remain draft-only according to policy

### Verification commands

- run the StrategySpec test module
- export the schema and inspect generated artifact

### Expected evidence

- changed files
- schema artifact path
- tests run and results
- remaining gaps

### Boundary/self-review checklist

- does StrategySpec remain backend/domain truth?
- did this avoid raw Python execution paths?
- did this avoid live order authority?

### Remaining gaps

- validator, compiler, runtime, and UX work are downstream seams

---

## `SAFE-01` — Hard-Rule Validator

- **Phase:** SAFE
- **Depends on:** `FND-01`
- **Unlocks:** `AI-01`, `UX-01`, `COMP-01`, `SYS-01`
- **Can run in parallel with:** `SAFE-02`

### Goal

Implement the StrategySpec hard-rule validator.

### Why this exists

Builder and AI outputs must be validated against explicit safety policy before they can proceed to compilation or runtime work.

### Prerequisites

- `FND-01`

### Scope included

- schema-aware safety validation
- forbidden execution-block checks
- raw-code bans
- parameter and risk policy checks

### Scope excluded

- compiler implementation
- runtime job orchestration

### Explicit non-goals

- inventing unsupported indicators/operators
- hidden bypass flags for AI or admin use

### Required files to create or change

- `packages/strategy_validation/validators.py`
- `packages/strategy_validation/policy.py`
- `packages/strategy_validation/reports.py`
- `tests/strategy_validation/test_forbidden_execution_blocks.py`
- `tests/strategy_validation/test_risk_required.py`
- `tests/strategy_validation/test_no_raw_code.py`

### Tests to add first or alongside

- forbidden calls fail
- raw Python fails
- missing risk block fails or is draft-only only
- lookahead/bar-close restrictions enforced

### Implementation constraints

- validator is the hard enforcement layer
- output must be durable/reportable
- validation must be repo-truth grounded, not UI-state grounded

### Verification commands

- run strategy validation tests

### Expected evidence

- changed files
- validation report example
- tests run and results

### Boundary/self-review checklist

- does this preserve the “no execution authority in Builder authoring surfaces” rule?
- does this reject forbidden operations explicitly?

### Remaining gaps

- registry-backed validation and compiler integration remain downstream

---

## `SAFE-02` — Adapter and Instrument Registry

- **Phase:** SAFE
- **Depends on:** `FND-01`
- **Unlocks:** `RUN-01`, `COMP-01`, `UX-01`, `SYS-01`
- **Can run in parallel with:** `SAFE-01`

### Goal

Implement adapter and instrument registry contracts for Builder-safe configuration.

### Why this exists

Strategies and backtests need approved adapter, venue, instrument, and data-range references grounded in backend-owned registry truth.

### Prerequisites

- `FND-01`

### Scope included

- adapter profile contracts
- instrument lookup interface
- safe backend selection metadata

### Scope excluded

- live credential handling
- direct exchange API calls

### Explicit non-goals

- inventing runtime adapters not grounded in NautilusTrader-facing dependencies
- loading live credentials into UX workflows

### Required files to create or change

- `packages/adapter_registry/models.py`
- `packages/adapter_registry/service.py`
- `packages/instrument_registry/service.py`
- `tests/adapter_registry/test_registry_lookup.py`
- `tests/instrument_registry/test_supported_instruments.py`

### Tests to add first or alongside

- supported adapter lookup passes
- invalid adapter/instrument combination fails
- unsupported venue or timeframe fails

### Implementation constraints

- backend owns discovery and lookup
- frontend consumes approved registry results only

### Verification commands

- run registry-related tests

### Expected evidence

- changed files
- sample adapter/instrument payloads
- tests run and results

### Boundary/self-review checklist

- are registry results backend-owned?
- does this avoid direct external credential or exchange coupling?

### Remaining gaps

- runtime and UX integrations remain downstream

---

## `RUN-01` — Async Backtest Job Runtime

- **Phase:** RUN
- **Depends on:** `FND-01`, `SAFE-02`
- **Unlocks:** `COMP-02`, `UX-02`, `SYS-01`
- **Can run in parallel with:** none

### Goal

Implement durable async backtest job orchestration.

### Why this exists

Builder must represent long-running backtests as backend-owned durable state rather than browser-owned activity.

### Prerequisites

- `FND-01`
- `SAFE-02`

### Scope included

- job records
- status transitions
- event persistence and replay hooks
- cancel request path via backend state

### Scope excluded

- compiler internals
- worker execution implementation details

### Explicit non-goals

- frontend-owned process lifetime
- websocket-dependent truth
- direct worker memory mutation from UI

### Required files to create or change

- `packages/backtest_jobs/models.py`
- `services/api/routes/backtests.py`
- `packages/runtime_events/models.py`
- `tests/backtest_jobs/test_create_job.py`
- `tests/backtest_jobs/test_runtime_persists_without_frontend.py`

### Tests to add first or alongside

- job creation is idempotent
- browser disconnect does not cancel durable state
- runtime events can be replayed

### Implementation constraints

- include exact StrategySpec version and adapter/instrument refs
- workers must consult backend state for cancellation

### Verification commands

- run backtest job and runtime event tests

### Expected evidence

- changed files
- example BacktestJob JSON
- tests run and results

### Boundary/self-review checklist

- is backend state authoritative?
- can the browser disappear without breaking runtime truth?

### Remaining gaps

- compile and worker execution seams remain downstream

---

## `COMP-01` — RuleGraphStrategy Compiler

- **Phase:** COMP
- **Depends on:** `FND-01`, `SAFE-01`, `SAFE-02`
- **Unlocks:** `COMP-02`, `SYS-01`
- **Can run in parallel with:** none

### Goal

Compile validated StrategySpec artifacts into safe RuleGraphStrategy compile artifacts.

### Why this exists

The compiler is the translation boundary between Builder strategy contracts and NautilusTrader execution-ready backtest artifacts.

### Prerequisites

- `FND-01`
- `SAFE-01`
- `SAFE-02`

### Scope included

- deterministic compile artifacts
- backtest profile output
- signal-preview-only live profile behavior

### Scope excluded

- worker execution runtime
- direct live order logic

### Explicit non-goals

- TradeAction generation
- submit_order paths
- unsupported custom execution DSLs

### Required files to create or change

- `packages/strategy_compiler/compiler.py`
- `packages/strategy_compiler/artifacts.py`
- `packages/nautilus_rule_graph/config.py`
- `packages/nautilus_rule_graph/strategy.py`
- `tests/strategy_compiler/test_compile_valid_spec.py`
- `tests/strategy_compiler/test_compile_hash_deterministic.py`
- `tests/strategy_compiler/test_live_profile_signal_only.py`

### Tests to add first or alongside

- valid spec compiles
- compile hash is stable
- unknown block fails
- live profile emits signal-preview artifacts only

### Implementation constraints

- deterministic output
- no live execution authority in compile artifacts

### Verification commands

- run compiler tests

### Expected evidence

- changed files
- sample compile artifact
- tests run and results

### Boundary/self-review checklist

- does the live profile avoid TradeAction/submit_order?
- is the compiler pure translation rather than runtime authority?

### Remaining gaps

- worker execution and promotion/governance remain downstream

---

## `COMP-02` — NautilusTrader Backtest Worker

- **Phase:** COMP
- **Depends on:** `RUN-01`, `COMP-01`
- **Unlocks:** `UX-02`, `SYS-01`
- **Can run in parallel with:** none

### Goal

Implement the NautilusTrader backtest worker for compiled Builder strategies.

### Why this exists

Backtests must run asynchronously from durable backend state and produce normalized result artifacts.

### Prerequisites

- `RUN-01`
- `COMP-01`

### Scope included

- worker runner
- config builder
- result normalization
- artifact persistence references

### Scope excluded

- live execution
- raw shell exposure

### Explicit non-goals

- loading live exchange credentials
- binding worker lifetime to frontend presence

### Required files to create or change

- `services/workers/nautilus_backtest_worker.py`
- `packages/backtest_runner/runner.py`
- `packages/backtest_runner/config_builder.py`
- `packages/backtest_runner/result_normalizer.py`
- `packages/backtest_runner/artifacts.py`
- `tests/backtest_runner/test_runner_dummy_data.py`
- `tests/backtest_runner/test_result_normalizer.py`
- `tests/backtest_runner/test_no_live_credentials.py`

### Tests to add first or alongside

- worker runs minimal fixture backtest
- result includes expected metrics/logs/trades artifacts
- no frontend connection is required
- no live credentials are loaded

### Implementation constraints

- use immutable StrategySpec version and compile hash snapshot
- persist runtime events and results as backend truth

### Verification commands

- run worker and result-normalizer tests

### Expected evidence

- changed files
- sample BacktestResult JSON
- tests run and results

### Boundary/self-review checklist

- is the worker detached from frontend session truth?
- does the worker avoid live credentials and shell exposure?

### Remaining gaps

- UX surfaces and governance/promotion remain downstream

---

## `UX-01` — Visual Strategy Builder UX

- **Phase:** UX
- **Depends on:** `FND-01`, `SAFE-01`, `SAFE-02`, `GOV-01`
- **Unlocks:** `AI-01`, `SYS-01`
- **Can run in parallel with:** `UX-02`

### Goal

Build the visual strategy builder MVP.

### Why this exists

Users need a visual authoring surface, but StrategySpec remains the persisted truth rather than UI graph state.

### Prerequisites

- `FND-01`
- `SAFE-01`
- `SAFE-02`
- `GOV-01`

### Scope included

- builder canvas
- block palette and inspector
- StrategySpec preview
- validation results integration

### Scope excluded

- runtime ownership
- unsupported execution blocks

### Explicit non-goals

- direct live execution controls
- storing canonical truth only in React state

### Required files to create or change

- `apps/web/components/strategy-builder/StrategyBuilderCanvas.tsx`
- `apps/web/components/strategy-builder/BlockPalette.tsx`
- `apps/web/components/strategy-builder/BlockInspector.tsx`
- `apps/web/components/strategy-builder/StrategySpecPreview.tsx`
- `tests/web/test_strategy_builder_serializes_spec.ts`

### Tests to add first or alongside

- visual edits serialize to StrategySpec
- unsupported blocks are unavailable
- validation errors are surfaced without becoming truth state

### Implementation constraints

- frontend edits draft authoring state only
- backend/domain objects remain canonical

### Verification commands

- run builder UI tests

### Expected evidence

- changed files
- screenshots or UI test results
- tests run and results

### Boundary/self-review checklist

- is StrategySpec still canonical?
- can UX create only supported safe blocks?

### Remaining gaps

- terminal, AI, and end-to-end verification remain downstream

---

## `UX-02` — Live Terminal and Job Console

- **Phase:** UX
- **Depends on:** `RUN-01`, `COMP-02`
- **Unlocks:** `SYS-01`
- **Can run in parallel with:** `UX-01`

### Goal

Build the terminal/job console as an observational surface over backend state.

### Why this exists

Users need to inspect status, logs, validation, and metrics without receiving raw shell access or runtime mutation authority.

### Prerequisites

- `RUN-01`
- `COMP-02`

### Scope included

- status and logs views
- progress/event replay
- request-cancel action via backend APIs

### Scope excluded

- shell access
- direct system command execution

### Explicit non-goals

- ssh/bash/python REPL access
- environment dumps or secret access

### Required files to create or change

- `apps/web/components/terminal/JobTerminal.tsx`
- `services/api/routes/runtime_events.py`
- `tests/web/test_job_terminal_replay.ts`
- `tests/runtime_events/test_replay_endpoint.py`

### Tests to add first or alongside

- reconnect replay works
- allowed commands only
- request cancel maps to backend durable state

### Implementation constraints

- terminal is not a shell
- commands are bounded status/help/metrics/validation interactions only

### Verification commands

- run terminal and runtime event replay tests

### Expected evidence

- changed files
- sample runtime event output
- tests run and results

### Boundary/self-review checklist

- is this terminal observational only?
- does it avoid shell and secret exposure?

### Remaining gaps

- AI flow and final verification remain downstream

---

## `AI-01` — AI Strategy Builder Flow

- **Phase:** AI
- **Depends on:** `FND-01`, `SAFE-01`, `SAFE-02`, `UX-01`, `GOV-01`
- **Unlocks:** `SYS-01`
- **Can run in parallel with:** none

### Goal

Implement the AI-assisted strategy drafting flow.

### Why this exists

AI is an advisory drafting surface that must produce StrategySpec drafts subject to the same safety and lifecycle rules as manual authoring.

### Prerequisites

- `FND-01`
- `SAFE-01`
- `SAFE-02`
- `UX-01`
- `GOV-01`

### Scope included

- AI draft request/response flow
- explanation and revision panel behavior
- validation feedback loop into draft authoring

### Scope excluded

- privileged bypasses
- direct runtime or order authority

### Explicit non-goals

- raw Python generation as canonical output
- skipping validator or lifecycle gates

### Required files to create or change

- `apps/web/components/ai-builder/AiStrategyCopilot.tsx`
- `apps/web/components/ai-builder/AiRevisionPanel.tsx`
- `apps/web/components/ai-builder/AiExplanationPanel.tsx`
- `services/api/routes/ai_builder.py`
- `tests/ai_builder/test_ai_output_must_validate.py`

### Tests to add first or alongside

- AI output becomes draft StrategySpec only
- invalid output is rejected or marked revision-needed
- AI cannot produce execution-only forbidden blocks

### Implementation constraints

- AI is advisory only
- all output must flow through validation and lifecycle rules

### Verification commands

- run AI builder tests

### Expected evidence

- changed files
- sample AI draft/validation flow
- tests run and results

### Boundary/self-review checklist

- does AI remain advisory?
- is every output forced through Builder safety contracts?

### Remaining gaps

- promotion contracts and final system verification remain downstream

---

## `GOV-01` — Lifecycle and Versioning

- **Phase:** GOV
- **Depends on:** `FND-01`
- **Unlocks:** `UX-01`, `AI-01`, `GOV-04`, `SYS-01`
- **Can run in parallel with:** `GOV-02`

### Goal

Implement Builder lifecycle and versioning rules.

### Why this exists

Draft, Testing, Beta, and Final states govern mutability, promotion eligibility, and evidence requirements.

### Prerequisites

- `FND-01`

### Scope included

- lifecycle models
- version freezing rules
- promotion policy contracts on the Builder side

### Scope excluded

- live execution authority
- Daedalus implementation work

### Explicit non-goals

- treating Final as live-trading permission
- bypassing immutable version requirements

### Required files to create or change

- `packages/lifecycle/models.py`
- `packages/lifecycle/state_machine.py`
- `packages/lifecycle/versioning.py`
- `packages/lifecycle/promotion_policy.py`
- `tests/lifecycle/test_versioning.py`
- `tests/lifecycle/test_promotion_policy.py`

### Tests to add first or alongside

- draft/editable behavior
- backtest-used version freeze
- beta/final freeze
- promotion requires evidence

### Implementation constraints

- lifecycle stage never grants direct live trading authority

### Verification commands

- run lifecycle tests

### Expected evidence

- changed files
- state transition examples
- tests run and results

### Boundary/self-review checklist

- does Final remain a frozen approved candidate only?
- is live authority still external to Builder?

### Remaining gaps

- registry/import, promotion contracts, and system verification remain downstream

---

## `GOV-02` — Repository and Dependency Setup

- **Phase:** GOV
- **Depends on:** none
- **Unlocks:** `FND-01`, `SAFE-02`, `COMP-02`
- **Can run in parallel with:** `GOV-01`

### Goal

Define and enforce repository and dependency boundaries for Nautilus Builder.

### Why this exists

Repo and dependency direction shape package layout and prevent entanglement with NautilusTrader or Nautilus-Daedalus.

### Prerequisites

- source-doc review of dependency architecture

### Scope included

- package/dependency rules
- version pinning policy
- Builder-only repo ownership

### Scope excluded

- edits to upstream NautilusTrader or Nautilus-Daedalus repos

### Explicit non-goals

- vendoring NautilusTrader
- making Builder depend on the full Daedalus runtime

### Required files to create or change

- dependency manifests
- architecture docs or package layout files needed to enforce the boundary
- tests or checks for dependency assumptions if applicable

### Tests to add first or alongside

- dependency pin/check coverage where practical

### Implementation constraints

- Builder depends on NautilusTrader directly
- Builder integrates with Daedalus through contracts/events/API only

### Verification commands

- run dependency or manifest checks if available

### Expected evidence

- changed files
- dependency summary
- checks run and results

### Boundary/self-review checklist

- does Builder stay independent of Daedalus repo internals?
- is NautilusTrader treated as upstream dependency only?

### Remaining gaps

- feature implementation and verification remain downstream

---

## `GOV-03` — Existing Strategy Registry and Safe Import

- **Phase:** GOV
- **Depends on:** `FND-01`, `SAFE-01`, `SAFE-02`, `GOV-01`
- **Unlocks:** `SYS-01`
- **Can run in parallel with:** `GOV-04`

### Goal

Implement Builder-side registry and safe import/fork handling for existing strategies.

### Why this exists

Builder should catalog Builder-native, Daedalus-origin, and raw NautilusTrader strategies without allowing unsafe direct editing or source coupling.

### Prerequisites

- `FND-01`
- `SAFE-01`
- `SAFE-02`
- `GOV-01`

### Scope included

- backend strategy catalog metadata
- read-only listing for external strategies
- safe import/fork path to new Draft StrategySpec when mappable

### Scope excluded

- direct editing of external runtime code
- browser-side source scanning

### Explicit non-goals

- importing unknown code as trusted StrategySpec automatically
- editing Daedalus strategies in place

### Required files to create or change

- `services/api/routes/strategy_registry.py`
- `packages/strategy_registry/models.py`
- `packages/strategy_registry/importer.py`
- `tests/strategy_registry/test_read_only_external_entries.py`
- `tests/strategy_registry/test_safe_import_to_draft.py`

### Tests to add first or alongside

- external entries are read-only
- safe import creates new Draft StrategySpec only
- incompatible source remains catalog-only

### Implementation constraints

- backend owns discovery/classification/safety checks

### Verification commands

- run strategy registry tests

### Expected evidence

- changed files
- sample catalog payload
- tests run and results

### Boundary/self-review checklist

- does UX stay out of external runtime code?
- are external strategies cataloged safely and read-only by default?

### Remaining gaps

- full system verification remains downstream

---

## `GOV-04` — Builder-Side Promotion Contract

- **Phase:** GOV
- **Depends on:** `GOV-01`, `COMP-01`
- **Unlocks:** `SYS-01`
- **Can run in parallel with:** `GOV-03`

### Goal

Define Builder-side shadow/promotion contracts without editing Daedalus.

### Why this exists

Builder must express promotion intent, evidence, and signal-preview boundaries while leaving live safety and execution authority external.

### Prerequisites

- `GOV-01`
- `COMP-01`

### Scope included

- promotion request models
- readiness reports
- Builder-side payloads, events, or API contracts
- mocks or fixtures for external integration boundaries

### Scope excluded

- Daedalus source changes
- live gate/execution-lane implementation

### Explicit non-goals

- Builder submitting live orders
- Builder importing execution-lane internals as direct dependencies

### Required files to create or change

- `packages/promotions/models.py`
- `packages/promotions/contracts.py`
- `packages/promotions/readiness.py`
- `tests/promotions/test_signal_preview_only_contract.py`
- `tests/promotions/test_promotion_requires_evidence.py`

### Tests to add first or alongside

- payload is signal-preview only
- promotion requires evidence
- no direct TradeAction/submit_order payloads exist

### Implementation constraints

- treat Daedalus as external boundary only
- Builder outputs contracts, not live authority

### Verification commands

- run promotion contract tests

### Expected evidence

- changed files
- sample readiness report
- sample contract payload
- tests run and results

### Boundary/self-review checklist

- is this seam Builder-only?
- does it stop before external execution authority?

### Remaining gaps

- full E2E verification remains downstream

---

## `SYS-01` — End-to-End MVP Verification

- **Phase:** SYS
- **Depends on:** `SAFE-01`, `SAFE-02`, `RUN-01`, `COMP-01`, `COMP-02`, `UX-01`, `UX-02`, `AI-01`, `GOV-01`, `GOV-03`, `GOV-04`
- **Unlocks:** `GOV-05`
- **Can run in parallel with:** none

### Goal

Run final end-to-end verification for the Nautilus Builder MVP.

### Why this exists

This prompt proves that the composed system preserves runtime, safety, lifecycle, and Builder-only integration boundaries.

### Prerequisites

- all dependent seams above

### Scope included

- end-to-end flow validation
- reconnect/runtime persistence checks
- validator and promotion boundary checks

### Scope excluded

- new feature additions discovered during verification

### Explicit non-goals

- ad hoc scope expansion under the cover of “verification”
- requiring Daedalus repo edits to complete the check

### Required files to create or change

- E2E tests and test fixtures needed for the verification flow
- verification report artifacts

### Tests to add first or alongside

- visual builder to StrategySpec flow
- API integration flow
- worker integration flow
- reconnect event replay test
- shadow/promotion boundary test

### Implementation constraints

- browser disconnect must not cancel backend truth
- Builder cannot submit orders
- promotion must stay signal-preview only on the Builder side

### Verification commands

- run the full E2E and integration test suite required for the MVP scenario

### Expected evidence

- changed files
- full E2E test report
- failed checks and fixes
- explicit safety statement for demo or candidate status

### Boundary/self-review checklist

- does the system preserve the “UX is not runtime owner” rule?
- does Builder stop short of live execution authority?

### Remaining gaps

- product polish beyond MVP remains out of scope

---

## `GOV-05` — Rename Product to Nautilus Builder Consistency Pass

- **Phase:** GOV
- **Depends on:** `SYS-01`
- **Unlocks:** none
- **Can run in parallel with:** none

### Goal

Perform a final consistency pass so product naming reflects Nautilus Builder across user-facing and architecture-facing artifacts.

### Why this exists

The doc set explicitly renames the product from Nautilus Strategy Lab to Nautilus Builder and this consistency should be maintained.

### Prerequisites

- `SYS-01`

### Scope included

- naming consistency in Builder-owned surfaces and docs

### Scope excluded

- unrelated copy rewrites
- external repo edits

### Explicit non-goals

- renaming external systems
- broad content refactoring unrelated to product naming

### Required files to create or change

- Builder-owned docs, UI labels, and configuration names as needed

### Tests to add first or alongside

- naming consistency checks where practical

### Implementation constraints

- preserve explicit distinction among Nautilus Builder, NautilusTrader, and Nautilus-Daedalus

### Verification commands

- run naming-related checks or searches where practical

### Expected evidence

- changed files
- summary of naming fixes
- checks run and results

### Boundary/self-review checklist

- are system names still semantically distinct?
- did the pass stay inside Builder-owned artifacts?

### Remaining gaps

- future branding work beyond current Builder scope remains out of scope
