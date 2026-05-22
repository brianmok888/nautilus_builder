# Nautilus Builder Prompt Pack Audit

## Purpose

This audit evaluates `doc/nautilus_builder_implementation_prompts.md` against the surrounding Nautilus Builder documentation and the approved prompt-system design.

The goal is to identify the gaps that must be fixed before the prompt pack can serve as a reliable, dual-mode execution system for coding agents.

## Scope

This audit is limited to the Nautilus Builder workspace.

- It does not modify product code.
- It does not assume or require edits in the Nautilus-Daedalus repository.
- Any Daedalus-related prompt is evaluated only for Builder-side contract safety and cross-repo coupling risk.

## Source Documents

- `doc/nautilus_builder_implementation_prompts.md`
- `doc/nautilus_builder_spec.md`
- `doc/nautilus_builder_implementation_plan.md`
- `doc/nautilus_builder_hardguards.md`
- `doc/nautilus_builder_directory_architecture.md`
- `doc/nautilus_builder_lifecycle_versioning.md`
- `doc/nautilus_builder_repo_dependency_architecture.md`
- `doc/nautilus_builder_existing_strategy_registry.md`
- `docs/superpowers/specs/2026-05-22-nautilus-builder-prompt-system-design.md`

## Audit Method

The audit checks the current prompt pack across six categories:

1. alignment with source docs;
2. sequencing and dependency correctness;
3. prompt scope quality;
4. verifiability;
5. portability across agent environments;
6. cross-repo coupling risk.

## Finding Format

Each finding uses:

- **Finding ID**
- **Severity**
- **Location**
- **Problem**
- **Why it matters**
- **Recommended fix**
- **Affected downstream prompts/docs**

## Findings

### Finding AUD-001

- **Severity:** critical
- **Location:** `doc/nautilus_builder_implementation_prompts.md` overall structure
- **Problem:** The prompt pack is a flat numbered list rather than an explicit execution system with phases, prerequisites, and dependency metadata.
- **Why it matters:** Agents can begin later prompts without established domain contracts, which increases the chance of broad, out-of-order implementation.
- **Recommended fix:** Replace flat numbering with stable phase-scoped IDs and add `depends_on`, `unlocks`, and optional parallelism metadata.
- **Affected downstream prompts/docs:** all prompts; execution design document; revised prompt pack

### Finding AUD-002

- **Severity:** major
- **Location:** `## How to Use These Prompts`
- **Problem:** The usage section assumes a specific skill stack (`nt`, `nt-architect`, `nt-ai-strategy-builder`, and others) without defining a tool-agnostic equivalent path.
- **Why it matters:** This makes the prompt pack less portable and mixes operating-environment assumptions into the core implementation instructions.
- **Recommended fix:** Split usage guidance into an OpenCode-aware path and a generic-agent path with identical acceptance criteria.
- **Affected downstream prompts/docs:** usage section; execution design document; revised prompt pack

### Finding AUD-003

- **Severity:** critical
- **Location:** Prompts 1-16 overall
- **Problem:** The current prompts do not declare prerequisites explicitly even though later prompts rely on earlier contract work such as StrategySpec, validators, registries, job state, and lifecycle semantics.
- **Why it matters:** Missing prerequisites make it easy to skip foundational work or implement UX/runtime seams before safety contracts are in place.
- **Recommended fix:** Add explicit prerequisite fields and phase ordering to every prompt.
- **Affected downstream prompts/docs:** all prompts; execution design document

### Finding AUD-004

- **Severity:** major
- **Location:** Prompt 10 — Daedalus Shadow Promotion Integration
- **Problem:** The title and framing suggest implementation may extend into Nautilus-Daedalus rather than clearly constraining work to Builder-side contracts and integration assumptions.
- **Why it matters:** This conflicts with the approved scope that Builder work must not require touching the Nautilus-Daedalus repository.
- **Recommended fix:** Rewrite this seam as a Builder-only promotion contract prompt, using external API/event assumptions, payload schemas, mocks, or fixtures rather than cross-repo edits.
- **Affected downstream prompts/docs:** Prompt 10; lifecycle/versioning prompts; execution design document

### Finding AUD-005

- **Severity:** major
- **Location:** Prompt 11 — End-to-End MVP Verification
- **Problem:** The scenario spans UX, API, worker runtime, reconnect behavior, validator logic, and promotion boundaries in one large verification block.
- **Why it matters:** This makes verification too broad for one bounded seam and hides which upstream prerequisites must be satisfied first.
- **Recommended fix:** Keep one final system verification prompt, but explicitly depend on prior phase completion and define sub-check categories inside the prompt contract.
- **Affected downstream prompts/docs:** Prompt 11; revised prompt pack; execution design document

### Finding AUD-006

- **Severity:** moderate
- **Location:** Prompt numbering
- **Problem:** The sequence jumps from Prompt 12 to Prompt 14, which suggests either a removed prompt or an undocumented gap.
- **Why it matters:** Numbering gaps reduce trust in the pack and make references less stable.
- **Recommended fix:** Move to stable semantic IDs rather than relying on flat integers.
- **Affected downstream prompts/docs:** all prompts; audit traceability; revised prompt pack

### Finding AUD-007

- **Severity:** major
- **Location:** Prompts 7-10 and 15
- **Problem:** Several prompts mix product behavior, runtime boundaries, and external integration assumptions without clearly separating included scope from excluded scope.
- **Why it matters:** Agents are more likely to overbuild or invent adjacent features when non-goals are not explicit.
- **Recommended fix:** Add standard `Scope included`, `Scope excluded`, and `Explicit non-goals` sections to each prompt.
- **Affected downstream prompts/docs:** revised prompt pack; execution design document

### Finding AUD-008

- **Severity:** major
- **Location:** Prompt deliverables overall
- **Problem:** The pack requires outputs like summaries, tests, and boundary review, but the structure and evidence expectations vary by prompt.
- **Why it matters:** Inconsistent evidence requirements make cross-prompt review harder and weaken verification discipline.
- **Recommended fix:** Normalize all prompts to one standard contract including files changed, tests added, commands run, verification output, assumptions, unresolved gaps, and boundary review.
- **Affected downstream prompts/docs:** all prompts; execution design document; revised prompt pack

### Finding AUD-009

- **Severity:** moderate
- **Location:** Prompts 1-6
- **Problem:** Early backend and runtime prompts identify required files and tests, but they do not always explain why each seam exists or what downstream work it unlocks.
- **Why it matters:** Agents with limited context may implement the minimum shape without preserving the architectural purpose or future dependency role.
- **Recommended fix:** Add `Why this exists` and `Unlocks` sections to each prompt.
- **Affected downstream prompts/docs:** foundation, safety, runtime, and compiler prompts

### Finding AUD-010

- **Severity:** major
- **Location:** Prompts 7-9
- **Problem:** UX and AI prompts rely on safety rules, StrategySpec contracts, and lifecycle boundaries but do not clearly restate the prerequisite relationship.
- **Why it matters:** This encourages premature UX implementation and increases the risk that frontend state becomes canonical.
- **Recommended fix:** Gate all UX and AI prompts on completed StrategySpec, validator, registry, and lifecycle prerequisites.
- **Affected downstream prompts/docs:** revised prompt pack phase ordering

### Finding AUD-011

- **Severity:** moderate
- **Location:** Prompt 15 — Existing Strategy Registry and Import
- **Problem:** The prompt likely sits at the intersection of Builder-native strategies, Daedalus catalog entries, and raw NautilusTrader imports, but the current pack does not strongly distinguish read-only cataloging from safe import/fork behavior.
- **Why it matters:** Without sharper boundaries, agents may broaden the feature into source scanning or direct editing workflows that conflict with the architecture docs.
- **Recommended fix:** Split or sharpen this prompt so read-only registry, safe import, and incompatible-source handling are explicit and bounded.
- **Affected downstream prompts/docs:** revised prompt pack; existing strategy registry seam

### Finding AUD-012

- **Severity:** moderate
- **Location:** Prompt 14 — Repository and Dependency Setup
- **Problem:** The prompt concerns repo/dependency policy but may be executed too late in the numbered sequence despite shaping package boundaries and dependency direction for the rest of the system.
- **Why it matters:** Repo-boundary mistakes are expensive to unwind after implementation work begins.
- **Recommended fix:** Move repo/dependency governance earlier as a governance seam or prerequisite reference for foundation work.
- **Affected downstream prompts/docs:** phase ordering; governance prompts; execution design

### Finding AUD-013

- **Severity:** major
- **Location:** Daedalus-related language across prompts and source docs references
- **Problem:** The pack correctly treats Daedalus as part of the broader system context, but it does not consistently distinguish external integration targets from editable implementation surfaces.
- **Why it matters:** This is the main route by which an agent could accidentally violate the Builder-only scope constraint.
- **Recommended fix:** Add a global Builder-only rule at the top of the revised pack and repeat it in any prompt that references promotion, shadow, signal-preview, or existing Daedalus strategies.
- **Affected downstream prompts/docs:** revised prompt pack; execution design document

### Finding AUD-014

- **Severity:** moderate
- **Location:** Acceptance tests across prompts
- **Problem:** Acceptance criteria are often meaningful but not always tied to explicit verification commands or artifact names.
- **Why it matters:** Agents may claim success without emitting reproducible evidence.
- **Recommended fix:** Require a `Verification commands` section and an `Expected evidence` section for every prompt.
- **Affected downstream prompts/docs:** all prompts; execution design document

## Summary of Highest-Priority Outcomes

The revised prompt system must address these top issues first:

1. convert the flat prompt list into a phased and dependency-aware execution system;
2. separate OpenCode-specific workflow instructions from generic-agent-compatible guidance;
3. make Daedalus-related seams Builder-only by design;
4. standardize prompt evidence and review expectations;
5. sharpen prompt boundaries so each unit owns one clean seam.

## Expected Downstream Changes

This audit implies three concrete follow-up actions:

- write an execution-design document that defines the phase model, prompt contract, dual-mode behavior, and Builder-only external-integration rules;
- rewrite the current prompt pack into stable-ID prompts with prerequisites and explicit non-goals;
- ensure every Daedalus-related seam is framed as a Builder-side contract, assumption, or integration boundary rather than a cross-repo implementation task.
