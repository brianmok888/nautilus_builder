# Nautilus Builder Prompt System Execution Design

## Purpose

This document defines how coding agents should execute the Nautilus Builder implementation prompt system.

It translates the approved prompt-system design into an operational contract that works in two environments:

- OpenCode-aware workflows with skills, subagents, and structured review loops
- generic coding-agent workflows without product-specific tooling

## Scope Rule

This execution design applies only inside the Nautilus Builder workspace.

- Build Nautilus Builder only.
- Do not modify or depend on edits in the Nautilus-Daedalus repository.
- Treat Daedalus as an external boundary for contracts, promotion requests, shadow or signal-preview assumptions, and external integration surfaces.

## Core Execution Principle

The prompt pack is a gated execution system, not a flat list of tasks.

Each prompt must:

- own one bounded seam;
- declare what must exist before it starts;
- declare what it unlocks next;
- identify what is out of scope;
- and emit concrete verification evidence.

In this document, an **execution graph** means the dependency-aware ordering formed by prompt IDs, prerequisites, unlocks, and allowed parallelism.

## Phase Model

The revised prompt pack should be grouped into these phases.

### Phase FND — Foundation Contracts

Purpose:

- define StrategySpec and adjacent foundational data contracts;
- establish immutable versioning fields and example artifacts;
- provide the domain truth that later phases depend on.

### Phase SAFE — Safety and Registry Layer

Purpose:

- enforce hard-rule validation;
- define adapter and instrument registries;
- encode allowed versus forbidden capabilities.

### Phase RUN — Runtime Orchestration

Purpose:

- define durable job ownership;
- establish event persistence and replay;
- isolate long-running backtests from frontend session state.

### Phase COMP — Compilation and Execution

Purpose:

- convert StrategySpec into safe compile artifacts;
- run backtests through NautilusTrader workers;
- enforce no direct live execution semantics.

### Phase UX — User-Facing Surfaces

Purpose:

- build authoring and observation interfaces;
- keep the frontend non-authoritative;
- surface only backend-owned truth.

### Phase AI — AI Drafting and Promotion Flows

Purpose:

- support AI-assisted strategy drafting;
- define promotion-related Builder-side contracts;
- preserve Builder-only scope for any Daedalus-facing seam.

### Phase GOV — Governance and System Finishing

Purpose:

- encode lifecycle/versioning policy;
- define repo and dependency boundaries;
- handle read-only external strategy registry/import rules;
- run final end-to-end verification.

Governance is split conceptually into two roles:

- **preflight governance**: repo/dependency and lifecycle constraints that must exist before some implementation seams begin;
- **finishing governance**: registry/import, promotion-boundary, and final verification work that closes the system without broadening feature scope.

## Phase Ordering Rules

The normal order is:

`GOV(preflight) → FND → SAFE → RUN → COMP → UX → AI → GOV(finishing)`

Rules:

1. No UX prompt may begin before required foundation, validation, and lifecycle prerequisites exist.
2. No AI prompt may bypass validation and lifecycle boundaries.
3. `GOV-02` may run before foundation work because it defines repo and dependency boundaries for later seams.
4. `GOV-01` may unlock downstream work before finishing-governance items are reached because lifecycle policy is an upstream contract.
5. No Daedalus-related prompt may become a cross-repo implementation task.
6. Final verification prompts must run only after required upstream seams are complete.

## Prompt Metadata Contract

Every prompt in the revised pack should include these metadata fields:

- `Prompt ID`
- `Phase`
- `Depends on`
- `Unlocks`
- `Can run in parallel with` (optional)

This metadata is required because it turns the pack into an execution graph rather than a loose prompt list.

## Standard Prompt Template

Each prompt must follow this structure.

### 1. Goal

What is being built.

### 2. Why this exists

Why the seam matters in the larger system.

### 3. Prerequisites

What contracts, files, or prior prompts must already exist.

### 4. Scope included

What the agent should do.

### 5. Scope excluded

What the agent must not do in this prompt.

### 6. Explicit non-goals

Important adjacent work that should not be invented or broadened into this seam.

### 7. Required files to create or change

Expected implementation touchpoints.

### 8. Tests to add first or alongside

Concrete tests or checks the agent must add or update.

### 9. Implementation constraints

Hard boundary rules, policy rules, and architecture constraints.

### 10. Verification commands

Concrete commands the agent should run to verify the work.

### 11. Expected evidence

Artifacts or outputs the agent must report, such as test output, JSON examples, reports, or boundary confirmations.

### 12. Boundary/self-review checklist

Short checklist confirming the work did not violate runtime, scope, or repo boundaries.

### 13. Remaining gaps

Explicitly list what was not done and what remains out of scope.

## Verification Rules

Every prompt execution must produce evidence, not just implementation claims.

Minimum required evidence:

- files created or changed;
- tests added or updated;
- commands run;
- verification output or summary;
- assumptions made;
- unresolved gaps;
- boundary review statement.

If a prompt cannot emit concrete evidence, it is incomplete.

`Runtime truth` means durable backend-owned state, persisted events, validator outcomes, compiler artifacts, and NautilusTrader backtest results rather than browser memory or transient UI state.

## Review Gates

Each prompt should pass two lightweight checks before downstream work proceeds:

1. **Spec-compliance gate**
   - Does the work satisfy the prompt goal and required constraints?

2. **Boundary-quality gate**
   - Does the work preserve runtime boundaries, repo boundaries, and scope discipline?

The revised prompt pack should instruct agents to report both gates explicitly.

## Dual-Mode Execution

### OpenCode-Aware Mode

This path may instruct agents to:

- use relevant skills and routers;
- use subagents for focused tasks;
- keep a todo list;
- perform structured review gates;
- and use platform-native verification workflows.

### Generic-Agent Mode

This path must express the same work without relying on platform-specific names.

Equivalent expectations:

- inspect repository truth first;
- plan before coding;
- add tests before or alongside implementation;
- avoid broad edits;
- run verification commands;
- report changed files and unresolved gaps.

### Compatibility Rule

The OpenCode-aware and generic-agent paths may differ in workflow richness, but they must not differ in:

- scope;
- acceptance criteria;
- safety boundaries;
- evidence requirements.

## Builder-Only Handling of Daedalus-Related Seams

Any prompt that references Daedalus must remain Builder-side only.

Allowed:

- Builder-owned payload schemas;
- Builder-owned promotion request models;
- Builder-owned readiness reports;
- mocked or stubbed responses that simulate external integration boundaries;
- read-only registry metadata stored in Builder;
- compatibility checks that stop before any Daedalus source change or runtime import.

Forbidden:

- editing Nautilus-Daedalus source files;
- importing Daedalus runtime internals as Builder implementation targets;
- making progress on the prompt contingent on cross-repo code changes;
- inventing live execution authority inside Builder.

## Parallelism Rules

Prompts may run in parallel only if:

- they depend on the same completed upstream contracts;
- they do not create competing truth models;
- they do not rely on unresolved safety-policy decisions.

Examples of likely safe parallelism:

- some UX surfaces after core contracts stabilize;
- some governance documentation prompts after core architecture is established.

`Safe parallelism` means concurrent work that cannot create competing truth models, cannot bypass unresolved policy decisions, and cannot force downstream rework when merged.

Examples of unsafe parallelism:

- compiler work before StrategySpec is stable;
- promotion work before lifecycle and safety boundaries are explicit;
- UX authoring work before validation and registry seams are defined.

## Prompt-Pack Naming Guidance

The revised pack should use stable semantic IDs, for example:

- `FND-01`
- `SAFE-01`
- `RUN-01`
- `COMP-01`
- `UX-01`
- `AI-01`
- `GOV-01`

This replaces fragile flat numbering and improves traceability from audit findings to rewritten prompts.

## Final ID Decisions

The revised pack intentionally finalizes a few IDs differently from the earliest design sketch:

- `COMP-02` is used for the NautilusTrader backtest worker because the seam belongs to compilation/execution rather than durable job orchestration.
- `GOV-04` is used for the Builder-side promotion contract because Builder must stop at governance/contract boundaries rather than own a live-execution phase.
- the separate rename pass was removed from the final pack and folded into system verification as a naming-consistency check against source docs.

## Completion Criteria for the Revised Prompt Pack

The prompt pack conforms to this execution design when:

- every prompt has phase and dependency metadata;
- every prompt uses the standard template;
- every prompt includes explicit exclusions and non-goals;
- every prompt defines evidence and boundary review expectations;
- and every Daedalus-related seam is Builder-only in implementation scope.
