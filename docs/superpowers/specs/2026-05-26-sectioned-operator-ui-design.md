# Sectioned Operator UI Design

## Purpose

Build the Nautilus Builder web UI section by section so the app feels like a compact operator command center instead of a scaffold. The workflow remains AI-assisted and NautilusTrader-aligned: operator words become StrategySpec drafts, drafts are validated, market data is selected, backtests produce evidence, results are reviewed, and execution-lane controls remain backend-gated and read-only in the browser.

## Approved section order

1. Dashboard / Home
2. AI Strategy Builder
3. StrategySpec Editor
4. Market + Dataset Setup
5. Backtest Center
6. Results / Research
7. Execution Lane / Config

## Constraints

- No browser-side API keys, exchange credentials, passwords, private keys, or signing material.
- No UI path may create `submit_order`, `TradeAction`, automatic promotion, or live execution authority.
- Execution lane controls are visibility/status surfaces only; profile/command authority remains backend-owned.
- NautilusTrader adapter/live-readiness claims require DataTester/ExecTester/reconciliation evidence. This UI segment does not add real venue connectivity.
- QuantDinger-style inspiration is limited to compact information architecture and operator workflow organization; no Vue migration and no QuickTrade/live-trade panel.

## Design

### Dashboard / Home

The home screen becomes the command center. It leads with a “Describe strategy” entry point, a single workflow trail (`AI → StrategySpec → Market data → Backtest → Review → Execution Lane`), compact progress cards, and quick anchors into the seven sections. The default active workspace remains AI prompt-first.

### AI Strategy Builder

The AI panel is framed as “Strategy intent” rather than generic prompt text. It includes prompt examples, an audit/lineage ID strip, validation-gate copy, rejected-draft error display, and a reminder that backtest remains separate.

### StrategySpec Editor

The editor is reorganized into a compact three-column/section layout: block canvas, inspector, and spec preview. Market/profile panels remain present but visually grouped so the editor reads as an editor instead of scattered cards.

### Market + Dataset Setup

The market panel becomes an explicit adapter/venue → instrument search → dataset profile → catalog guard flow. It keeps backend profile validation and makes catalog/profile readiness visible before backtest.

### Backtest Center

The backtest page gains a run configuration summary, job status card, observational terminal, and artifact manifest placeholders. It remains evidence-only and shows `may_submit_order: false`.

### Results / Research

Results render metric cards, existing trades/fills/logs/artifacts, and chart placeholders for equity/drawdown until a chart library is deliberately added. Research notes remain observational.

### Execution Lane / Config

The execution config section is labeled “Execution Lane / Config” and presents a read-only feature visibility matrix, venue binding, and explicit paper/live controls visibility-only language.

## Testing plan

- Python UI contract tests scan each section for required labels and forbidden authority/credential strings.
- Vitest renders the dashboard command center and verifies prompt-first navigation labels.
- Existing component tests for AI, market, strategy builder, results, config, and E2E must stay passing.

## Stop condition

This segment is complete when all seven sections expose the new UI language, tests/build/E2E pass, docs are reconciled, and the branch is committed/pushed. It must not claim real live venue connectivity.
