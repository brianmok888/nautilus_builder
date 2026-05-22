# Nautilus Builder Prompt System Design

## Purpose

This document defines how to audit, redesign, and operationalize `doc/nautilus_builder_implementation_prompts.md` as a maintainable prompt system for building Nautilus Builder.

The target outcome is a three-document set:

1. an audit of the current prompt pack;
2. an execution design for how agents should use the prompt system; and
3. a revised prompt pack aligned to that execution design.

## Scope Boundary

This work is limited to the Nautilus Builder workspace.

- Build Nautilus Builder.
- Do not modify or touch the Nautilus-Daedalus repository.
- Daedalus may be referenced only as an external boundary, integration target, or contract surface.
- Any Daedalus-related prompt must be executable from the Builder side only, using contracts, mocks, fixtures, or integration placeholders rather than cross-repo edits.

## Source Documents

The design is derived from these local documents:

- `doc/nautilus_builder_spec.md`
- `doc/nautilus_builder_implementation_plan.md`
- `doc/nautilus_builder_hardguards.md`
- `doc/nautilus_builder_directory_architecture.md`
- `doc/nautilus_builder_lifecycle_versioning.md`
- `doc/nautilus_builder_repo_dependency_architecture.md`
- `doc/nautilus_builder_existing_strategy_registry.md`
- `doc/nautilus_builder_implementation_prompts.md`

The core boundary preserved throughout is:

- UX is authoring and observation only;
- NautilusTrader is runtime and backtest truth;
- Daedalus is an external live safety and control-plane boundary;
- Nautilus Builder must not move runtime ownership into the frontend.

## Problem Statement

The current `nautilus_builder_implementation_prompts.md` is valuable but overloaded.

It currently mixes several roles:

- execution instructions for coding agents;
- sequencing information from the implementation plan;
- architectural boundary reminders from the spec and hardguards;
- and prompt-level file and test requirements.

This produces four main problems:

1. the file is too flat, so dependencies between prompts are not explicit enough;
2. OpenCode-specific and generic-agent assumptions are mixed together;
3. some prompts appear broader than one clean implementation seam;
4. the verification/reporting contract is not normalized across all prompts.

## Recommended Deliverable Set

### 1. Audit Document

Purpose: evaluate the current prompt pack.

The audit should capture:

- contradictions with source documents;
- missing sequencing or prerequisite information;
- prompts that span multiple responsibilities;
- weak verification or acceptance criteria;
- OpenCode-specific assumptions that should be isolated;
- and any cross-repo coupling to Nautilus-Daedalus that must be removed.

This document is diagnostic only.

### 2. Execution Design Document

Purpose: define how the prompt system must be used.

This document should specify:

- the canonical phase order;
- prompt prerequisites and dependency rules;
- a fixed prompt output contract;
- review and verification gates;
- bounded-scope rules;
- dual-mode execution behavior for OpenCode-aware and generic agents;
- and the Builder-only implementation rule for Daedalus-facing seams.

This document is the operating contract.

### 3. Revised Prompt Pack

Purpose: provide the executable prompts.

The revised prompt pack should:

- be phase-scoped rather than just flat-numbered;
- use stable prompt IDs;
- declare dependencies explicitly;
- define included scope and excluded scope;
- require tests and verification evidence;
- and preserve compatibility with both OpenCode-aware and generic coding agents.

This document is the execution layer.

## Architecture of the Prompt System

The prompt system should be treated as a gated workflow, not a flat list.

### Core Rule

Each prompt must:

- represent one bounded seam;
- declare its prerequisites;
- emit concrete verification evidence;
- and confirm boundary compliance before downstream prompts proceed.

### Recommended Phases

#### Phase 1: Foundation Contracts

Examples:

- StrategySpec schema and models;
- enums and validation flags;
- example specs;
- versioning primitives.

#### Phase 2: Safety and Registry Layer

Examples:

- hard-rule validator;
- adapter registry;
- instrument registry;
- allowed and forbidden capability mappings.

#### Phase 3: Runtime Orchestration

Examples:

- BacktestJob contracts;
- worker queue ownership;
- runtime event persistence and replay;
- artifact persistence boundaries.

#### Phase 4: Compilation and Execution

Examples:

- StrategySpec to RuleGraphStrategy compiler;
- NautilusTrader backtest worker;
- execution restriction enforcement.

#### Phase 5: UX Surfaces

Examples:

- visual strategy builder;
- terminal and job console;
- result inspection views;
- runtime-safe observational UI behavior.

#### Phase 6: AI and Promotion Flows

Examples:

- AI strategy drafting flow;
- shadow or signal-preview promotion flows;
- lifecycle and versioning enforcement;
- existing strategy registry or import paths.

#### Phase 7: System Verification and Governance

Examples:

- end-to-end MVP verification;
- repository and dependency alignment;
- naming consistency and product rename checks.

## Dual-Mode Execution Design

The prompt system should target two execution environments without changing implementation intent.

### OpenCode-Aware Path

This variant may reference:

- skills and routers;
- subagents;
- todo discipline;
- explicit review gates;
- and OpenCode-native verification workflow.

### Generic-Agent Path

This variant must restate the same work in tool-agnostic form, such as:

- inspect repository truth first;
- plan before coding;
- add tests first or alongside implementation;
- report changed files;
- run concrete verification commands;
- and report unresolved gaps.

### Compatibility Rule

The OpenCode-aware path may be richer in execution guidance, but it must not alter:

- implementation scope;
- acceptance criteria;
- safety boundaries;
- or required evidence.

## Revised Prompt-Pack Shape

### Stable Prompt IDs

Replace flat numbering with stable IDs such as:

- `FND-01` StrategySpec schema and models
- `SAFE-01` hard-rule validator
- `SAFE-02` adapter and instrument registry
- `RUN-01` async backtest job runtime
- `COMP-01` RuleGraphStrategy compiler
- `RUN-02` NautilusTrader backtest worker
- `UX-01` visual strategy builder
- `UX-02` live terminal and job console
- `AI-01` AI strategy builder flow
- `LIVE-01` shadow promotion integration contract
- `SYS-01` end-to-end MVP verification
- `GOV-01` lifecycle and versioning
- `GOV-02` repository and dependency setup
- `GOV-03` existing strategy registry or import
- `GOV-04` product rename consistency

### Dependency Metadata

Each prompt should declare:

- `depends_on`
- `unlocks`
- `can_run_in_parallel_with` when safe

### Scope Controls

Each prompt should define:

- included scope;
- excluded scope;
- explicit non-goals;
- and repo-boundary constraints.

This is especially important to prevent agents from inventing live execution features, raw Python authoring, or unsupported cross-repo changes.

### Auditability Hooks

Each prompt should require agents to report:

- files changed;
- tests added;
- commands run;
- verification output;
- assumptions made;
- unresolved gaps;
- and a short boundary review.

## Standard Prompt Contract

Every prompt in the revised pack should follow the same template.

1. Goal
2. Why this exists
3. Prerequisites
4. Scope included
5. Scope excluded
6. Required files to create or change
7. Tests to add first or alongside
8. Implementation constraints
9. Verification commands
10. Expected evidence
11. Boundary or self-review checklist
12. Remaining gaps and explicit non-goals

This keeps prompts comparable and auditable.

## Audit Design

The audit should use explicit categories.

### 1. Alignment With Source Docs

Check consistency against the spec, implementation plan, hardguards, directory architecture, lifecycle rules, and dependency architecture.

### 2. Sequencing and Dependency Correctness

Check that prompts establish foundational contracts before runtime, UX, AI, or promotion work depends on them.

### 3. Prompt Scope Quality

Check whether each prompt is one bounded seam or an over-broad mixed concern.

### 4. Verifiability

Check whether prompts require measurable evidence rather than implementation claims.

### 5. Portability

Check where prompts are overly tied to one agent environment.

### 6. Cross-Repo Coupling

Check for any prompt that assumes direct code changes in Nautilus-Daedalus.

Those must be rewritten into Builder-only contracts, mocks, fixtures, or external integration assumptions.

### Audit Finding Format

Each finding should use a stable structure:

- Finding ID
- Severity
- Location
- Problem
- Why it matters
- Recommended fix
- Affected downstream prompts or docs

## Explicit Constraint for Daedalus-Related Work

Daedalus-related prompts must be rewritten to preserve Builder-only implementation scope.

Allowed:

- Builder-side interface assumptions;
- Builder-side payload schemas;
- promotion request contracts;
- mocked or stubbed external integrations;
- readiness checks that stop at documented external boundaries.

Forbidden:

- editing Nautilus-Daedalus code;
- requiring direct Daedalus repo internals as implementation targets;
- coupling Builder progress to cross-repo edits;
- or defining prompts that are only completable by modifying Daedalus.

## Recommended Outcome

The final design should produce:

1. an audit document that explains what is wrong or missing in the current prompt pack;
2. an execution design document that defines the operating model for dual-mode agent execution; and
3. a revised prompt pack that is modular, phase-aware, dependency-aware, auditable, and Builder-only in implementation scope.

## Approval Outcome Captured

This design reflects the approved direction:

- deliver a full doc set: audit + execution design + revised prompt pack;
- support dual-mode execution;
- build Nautilus Builder;
- and do not touch the Nautilus-Daedalus repository.
