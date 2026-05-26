# Sectioned Operator UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the Nautilus Builder UI section by section into a compact operator workflow covering dashboard, AI builder, StrategySpec editor, market/dataset setup, backtest center, results/research, and execution config.

**Architecture:** Keep the existing Next.js + Ant Design React shell. Improve existing components in place and add only focused tests/docs; no new frontend dependencies and no backend live-order changes.

**Tech Stack:** Next.js app router, React 19, Ant Design React, Vitest, Playwright, pytest contract scans.

---

### Task 1: Contract tests for sectioned UI

**Files:**
- Create: `tests/web/test_sectioned_operator_ui.py`
- Create: `apps/web/components/dashboard/BuilderDashboard.test.tsx`

- [x] **Step 1: Write failing tests** checking all seven UI section labels and forbidden authority/credential tokens.
- [x] **Step 2: Verify RED** with `pytest tests/web/test_sectioned_operator_ui.py -q` and `cd apps/web && npm test -- --run components/dashboard/BuilderDashboard.test.tsx`.

### Task 2: Dashboard / Home

**Files:**
- Modify: `apps/web/components/dashboard/BuilderDashboard.tsx`

- [x] Add command-center hero copy, workflow trail, compact progress cards, quick CTA buttons, and seven-section anchors.
- [x] Run `cd apps/web && npm test -- --run components/dashboard/BuilderDashboard.test.tsx` and verify green.

### Task 3: AI Strategy Builder

**Files:**
- Modify: `apps/web/components/ai-builder/AiStrategyCopilot.tsx`

- [x] Rename prompt section to Strategy intent, add prompt examples and validation-gate copy, and keep accepted-only Apply behavior.
- [x] Run `pytest tests/web/test_sectioned_operator_ui.py::test_ai_builder_section_guides_prompt_to_validated_draft_without_authority -q` and existing AI Vitest.

### Task 4: StrategySpec Editor

**Files:**
- Modify: `apps/web/components/strategy-builder/StrategyBuilderWorkspace.tsx`
- Modify: `apps/web/app/globals.css`

- [x] Group editor surfaces into compact editor layout with block canvas, inspector, and spec preview labels.
- [x] Run strategy-builder Vitest and contract scan.

### Task 5: Market + Dataset Setup

**Files:**
- Modify: `apps/web/components/market/MarketProfilePanel.tsx`

- [x] Add section labels for adapter/venue, instrument search, dataset profile, catalog guard, and validate dataset profile.
- [x] Preserve API payload shape and run market profile Vitest.

### Task 6: Backtest Center

**Files:**
- Modify: `apps/web/app/backtests/[jobId]/page.tsx`

- [x] Add run configuration, job status, artifact manifest, observational terminal, and no-order labels.
- [x] Run page contract scan and Playwright after all sections.

### Task 7: Results / Research

**Files:**
- Modify: `apps/web/components/results/ResultsDashboard.tsx`

- [x] Add metric cards label, equity/drawdown chart placeholders, research notes, and chart-library-later language.
- [x] Preserve existing payload rendering and Vitest assertions.

### Task 8: Execution Lane / Config

**Files:**
- Modify: `apps/web/components/config/ExecutionLaneFeaturePanel.tsx`

- [x] Add execution config title, feature visibility matrix, venue binding label, paper/live visibility-only copy, and no-browser-credentials language.
- [x] Preserve secret-free read-only UI behavior.

### Task 9: Docs and verification

**Files:**
- Modify: `structure.md`
- Modify: `findings.md`
- Modify: `handguard.md`

- [x] Record segment completion and guardrails.
- [x] Run `git diff --check`, Python contract suite, frontend typecheck, Vitest, build, Playwright, and high audit gate.
- [x] Commit using Lore protocol and push `origin/master`.
