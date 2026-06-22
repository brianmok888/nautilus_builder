# ADR 0004: UI virtualization (TanStack Virtual) — DEFERRED

- **Status:** Deferred (adopt only on trigger)
- **Date:** 2026-06-22
- **Adoption Report reference:** §3.3

## Context

The Adoption Report §3.3 recommended TanStack Virtual "tactically, only for
large scroll surfaces" (backtest trades, fills, event logs, evidence ledger
entries, audit events, TradeHUD replay streams).

## Decision

**Defer adoption** until a proven large-list rendering performance problem
exists. Current UI surfaces are pagination-controlled and do not exhibit jank.

## Rationale

The primary list surface (`ResultsListClient.tsx`) uses Ant Design Table with
`pagination={{ pageSize: 20 }}`. It never renders more than 20 rows at once.
Virtualization provides no meaningful benefit below ~500 simultaneously-rendered
rows; adding it now would be premature complexity (report §3.3 explicitly warns
against "premature complexity if used everywhere").

## Trigger condition (when to adopt)

Adopt TanStack Virtual for a specific surface when ALL of these are true:
1. A list renders 500+ rows simultaneously without pagination or
   "load more" controls.
2. Measurable render jank is observed (frame drops on scroll).
3. The list is a read-only display surface (results, evidence, logs, events).

When adopted, wrap it in a small internal `apps/web/lib/virtual/VirtualList.tsx`
component (report §3.3) to keep dependency churn contained. Do NOT rewrite the
Ant Design design system.

## Guardrails (if/when adopted)

- Only large views use virtualization; small lists/cards/forms remain unchanged.
- Ant Design remains the design system (no Tailwind/Headless rewrite).
- No breaking changes to frontend contract tests.
