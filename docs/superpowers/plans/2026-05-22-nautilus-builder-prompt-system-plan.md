# Nautilus Builder Prompt System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax and are intended to be completed in order. Do not skip verification steps. Do not broaden scope. Keep all work inside the Nautilus Builder workspace.

## Goal

Produce the approved three-document set for the Nautilus Builder prompt system:

1. `audit` of the current `doc/nautilus_builder_implementation_prompts.md`
2. `execution design` for how the prompt system should be used
3. `revised prompt pack` aligned to the execution design

## Hard Scope Constraints

- Work only in the current Nautilus Builder repository root or an isolated worktree created from it
- Do **not** modify, read from for implementation decisions beyond already-captured boundary assumptions, or otherwise touch the Nautilus-Daedalus repository
- Daedalus-related content must stay Builder-side only: contracts, integration assumptions, mocks, fixtures, and external-boundary notes
- Do not add implementation code for Nautilus Builder product features in this plan; this plan is only for the prompt-system document set

## Required Inputs

- `doc/nautilus_builder_implementation_prompts.md`
- `doc/nautilus_builder_spec.md`
- `doc/nautilus_builder_implementation_plan.md`
- `doc/nautilus_builder_hardguards.md`
- `doc/nautilus_builder_directory_architecture.md`
- `doc/nautilus_builder_lifecycle_versioning.md`
- `doc/nautilus_builder_repo_dependency_architecture.md`
- `doc/nautilus_builder_existing_strategy_registry.md`
- `docs/superpowers/specs/2026-05-22-nautilus-builder-prompt-system-design.md`

## Planned Outputs

- `docs/superpowers/audits/2026-05-22-nautilus-builder-prompt-pack-audit.md`
- `docs/superpowers/designs/2026-05-22-nautilus-builder-prompt-system-execution-design.md`
- `docs/superpowers/prompts/2026-05-22-nautilus-builder-implementation-prompts-revised.md`

## File Structure Map

### Existing inputs

- `doc/nautilus_builder_implementation_prompts.md`
  - Current flat prompt pack to audit and redesign
- `docs/superpowers/specs/2026-05-22-nautilus-builder-prompt-system-design.md`
  - Approved design spec and source of truth for this plan

### New outputs

- `docs/superpowers/audits/2026-05-22-nautilus-builder-prompt-pack-audit.md`
  - Structured findings against source docs, execution quality, portability, and cross-repo coupling
- `docs/superpowers/designs/2026-05-22-nautilus-builder-prompt-system-execution-design.md`
  - The operating contract for prompt phases, dependencies, dual-mode behavior, and prompt template
- `docs/superpowers/prompts/2026-05-22-nautilus-builder-implementation-prompts-revised.md`
  - The rewritten prompt pack with stable IDs, dependencies, explicit exclusions, and verification contract

## Implementation Strategy

Deliver the work in three bounded passes:

1. Audit the current prompt pack against source documents and approved scope
2. Write the execution design that fixes the identified structural problems
3. Rewrite the prompt pack to conform to the new execution design

Each pass must end with a verification read-through before moving to the next pass.

## Task 1 — Prepare directories and confirm inputs

- [ ] Verify the spec file exists at `docs/superpowers/specs/2026-05-22-nautilus-builder-prompt-system-design.md`
- [ ] Verify the current prompt pack exists at `doc/nautilus_builder_implementation_prompts.md`
- [ ] Create `docs/superpowers/audits/` if missing
- [ ] Create `docs/superpowers/designs/` if missing
- [ ] Create `docs/superpowers/prompts/` if missing
- [ ] Re-read the approved spec and list the non-negotiable scope constraints in working notes
- [ ] Re-read the current prompt pack headings and prompt boundaries before drafting findings

### Verification

- [ ] Confirm all target output directories exist
- [ ] Confirm the list of required inputs matches the approved spec

## Task 2 — Build the audit skeleton

- [ ] Create `docs/superpowers/audits/2026-05-22-nautilus-builder-prompt-pack-audit.md`
- [ ] Add a short purpose section explaining what is being audited and why
- [ ] Add a scope section that explicitly forbids touching Nautilus-Daedalus
- [ ] Add a source-documents section listing all Builder docs used for the audit
- [ ] Add an audit-method section describing how findings are derived
- [ ] Add a findings-format section with: Finding ID, Severity, Location, Problem, Why it matters, Recommended fix, Affected downstream prompts/docs

### Verification

- [ ] Re-read the audit skeleton and confirm the finding format is consistent with the approved spec

## Task 3 — Fill alignment and sequencing findings

- [ ] Compare the current prompt pack to `doc/nautilus_builder_spec.md`
- [ ] Record findings for any mismatch with UX/runtime boundaries
- [ ] Compare the current prompt pack to `doc/nautilus_builder_implementation_plan.md`
- [ ] Record findings for missing or unclear sequencing and prerequisites
- [ ] Compare the current prompt pack to `doc/nautilus_builder_hardguards.md`
- [ ] Record findings for safety-boundary drift or missing constraints
- [ ] Compare the current prompt pack to lifecycle, dependency, and existing-strategy docs
- [ ] Record findings for versioning, repo-boundary, or import-boundary gaps

### Verification

- [ ] Re-read all alignment findings and confirm each one references a specific source doc or section

## Task 4 — Fill scope, portability, and cross-repo findings

- [ ] Identify prompts that mix multiple seams in one task
- [ ] Record findings where required files or acceptance tests are too broad or underspecified
- [ ] Record findings where OpenCode-specific instructions are mixed into otherwise generic prompts
- [ ] Record findings where a generic agent would lack enough operational guidance
- [ ] Record findings for any Daedalus-coupled prompt that assumes cross-repo edits
- [ ] Add a short summary section grouping the highest-priority audit outcomes

### Verification

- [ ] Re-read the full audit and confirm every finding leads to a concrete downstream rewrite action

## Task 5 — Draft the execution design skeleton

- [ ] Create `docs/superpowers/designs/2026-05-22-nautilus-builder-prompt-system-execution-design.md`
- [ ] Add purpose and scope sections
- [ ] Add Builder-only and no-Daedalus-edit rule near the top
- [ ] Add a phase model section
- [ ] Add a prompt contract section
- [ ] Add a dual-mode execution section
- [ ] Add a review-and-verification gates section

### Verification

- [ ] Re-read the execution-design skeleton and confirm all major sections from the approved spec are present

## Task 6 — Complete the execution design

- [ ] Define the phase order: foundation, safety, runtime, compilation, UX, AI/promotion, system verification/governance
- [ ] Define prerequisite rules between phases and between prompts
- [ ] Define allowed parallelism rules for independent prompts
- [ ] Define the fixed prompt template fields
- [ ] Define the OpenCode-aware execution path
- [ ] Define the generic-agent execution path
- [ ] Add the compatibility rule that acceptance criteria must not differ across modes
- [ ] Add the Builder-only treatment for Daedalus-facing prompts
- [ ] Add explicit non-goals to prevent product-feature overbuild and repo drift

### Verification

- [ ] Re-read the execution design against the audit summary and confirm it addresses the identified structural problems

## Task 7 — Draft the revised prompt-pack skeleton

- [ ] Create `docs/superpowers/prompts/2026-05-22-nautilus-builder-implementation-prompts-revised.md`
- [ ] Add a short “how to use this pack” section
- [ ] Add the Builder-only scope rule and Daedalus integration rule
- [ ] Add a stable-ID naming convention section
- [ ] Add a standard prompt template section
- [ ] Add a phase index listing all prompt IDs in execution order

### Verification

- [ ] Re-read the phase index and confirm it covers the same overall problem space as the current prompt pack without broadening scope

## Task 8 — Rewrite the prompts phase by phase

- [ ] Rewrite foundation prompts with stable IDs and explicit prerequisites
- [ ] Rewrite safety and registry prompts with explicit exclusions and verification evidence
- [ ] Rewrite runtime orchestration prompts with durable-state and replay boundaries
- [ ] Rewrite compiler and worker prompts with Builder-only constraints and no live-execution broadening
- [ ] Rewrite UX prompts so frontend remains observational and non-authoritative
- [ ] Rewrite AI and promotion prompts so any Daedalus reference is contract-only
- [ ] Rewrite governance prompts for lifecycle, repo boundaries, import, and rename consistency

### Verification

- [ ] Re-read each rewritten prompt and confirm it uses the standard template fields
- [ ] Confirm each prompt has explicit non-goals
- [ ] Confirm each prompt states required evidence and boundary review expectations

## Task 9 — Cross-check the revised prompt pack against the audit

- [ ] For each major audit finding, verify the revised prompt pack addresses it directly
- [ ] Verify all known cross-repo coupling issues have been converted to Builder-only interfaces or assumptions
- [ ] Verify OpenCode-specific guidance is isolated from the generic-agent-compatible core instructions
- [ ] Verify sequencing is explicit through `depends_on`, `unlocks`, or phase ordering
- [ ] Add a short traceability section mapping major audit categories to redesign changes

### Verification

- [ ] Re-read the traceability section and confirm no major audit category is left unresolved without explanation

## Task 10 — Final self-review of all three documents

- [ ] Scan all three files for placeholders like `TODO`, `TBD`, or unfinished notes
- [ ] Scan for contradictions between the audit, execution design, and revised prompt pack
- [ ] Check that no section implies touching Nautilus-Daedalus
- [ ] Check that no section changes the approved 3-document deliverable shape
- [ ] Check that filenames, dates, and internal references are correct

### Verification

- [ ] Re-read all three files end-to-end
- [ ] Confirm the wording stays within Builder workspace scope

## Task 11 — Final delivery summary

- [ ] Prepare a summary listing the three created files
- [ ] Summarize the biggest audit findings in 3-5 bullets
- [ ] Summarize the execution model changes in 3-5 bullets
- [ ] Summarize the revised prompt-pack changes in 3-5 bullets
- [ ] List any remaining open questions or intentionally deferred issues

## Suggested Verification Commands

Run these as applicable while implementing the plan:

- [ ] Read the current prompt pack and source docs before drafting each output
- [ ] Search the output files for placeholders (`TODO`, `TBD`, `FIXME`)
- [ ] Search the output files for accidental Nautilus-Daedalus repo-edit language
- [ ] Re-read generated files after each major write step

## Definition of Done

This plan is complete when:

- the audit exists and contains structured, actionable findings;
- the execution design exists and defines the dual-mode operating contract;
- the revised prompt pack exists and follows the new prompt template and phase model;
- all three documents remain Builder-only in implementation scope;
- and no document requires or implies modifying the Nautilus-Daedalus repository.
