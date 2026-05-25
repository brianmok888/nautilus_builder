# Frontend UI/API Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix VM staging JSON/proxy failures and make Nautilus Builder render as a styled no-dependency operator dashboard.

**Architecture:** Keep `apps/web/lib/api.ts` as the fetch boundary and add safe response parsing/error diagnostics there. Add `apps/web/app/globals.css` as a small design system imported by `layout.tsx`; apply class names to existing semantic pages/components without adding runtime authority.

**Tech Stack:** Next.js app router, React 19, TypeScript, Vitest, Python source-contract tests, CSS only.

---

### Task 1: API JSON/proxy error handling

**Files:**
- Create: `apps/web/lib/api.test.ts`
- Modify: `apps/web/lib/api.ts`

- [ ] **Step 1: Write failing Vitest tests** for non-JSON HTTP responses, empty errors, and network failures.
- [ ] **Step 2: Run** `cd apps/web && npm test -- --run lib/api.test.ts`; expected RED against unconditional `response.json()`.
- [ ] **Step 3: Implement safe parsing** with content-type checks, text snippets, status `0` network errors, and richer `ApiError` fields.
- [ ] **Step 4: Run** the same Vitest test; expected GREEN.

### Task 2: No-dependency visual shell

**Files:**
- Create: `apps/web/app/globals.css`
- Modify: `apps/web/app/layout.tsx`
- Modify: `apps/web/app/page.tsx`
- Modify selected `apps/web/components/**` and route pages only for class names/visual grouping.
- Modify: `tests/web/test_app_shell_contract.py`
- Modify: `tests/web/test_frontend_infrastructure.py`

- [ ] **Step 1: Write failing Python source-contract tests** requiring `./globals.css` import and shell/style tokens.
- [ ] **Step 2: Run** `rtk pytest tests/web/test_app_shell_contract.py tests/web/test_frontend_infrastructure.py -q`; expected RED.
- [ ] **Step 3: Implement CSS and class names** for page shell, dashboard grid, cards, panels, nav, form controls, terminal/status badges.
- [ ] **Step 4: Run** the focused Python tests; expected GREEN.

### Task 3: Reconciliation and verification

**Files:**
- Modify: `structure.md`
- Modify: `findings.md`
- Modify: `handguard.md`

- [ ] **Step 1: Update review artifacts** with segment completions, verification evidence, and remaining risk.
- [ ] **Step 2: Run** `rtk pytest tests/web tests/integration -q`.
- [ ] **Step 3: Run** `cd apps/web && npm run typecheck && npm test && npm run build`.
- [ ] **Step 4: Run** `git diff --check` and inspect `git status`.
- [ ] **Step 5: Code-review the diff**, fix any findings, then commit and push with Lore protocol.
