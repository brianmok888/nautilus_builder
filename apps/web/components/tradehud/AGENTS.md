# AGENTS — apps/web/components/tradehud

The live TradeHUD panel set — the observational runtime monitor UI. ~25 TSX panels mounted by `apps/web/app/tradehud/page.tsx` via `TradeHudShell`.

## Scope (panel groups)
- **Shell/layout**: `TradeHudShell.tsx` (root layout + feed wiring), `TradeHudTopBar.tsx`, `TradeTape.tsx`, `LaneHealthStrip.tsx`.
- **Market**: `OrderBookLadder.tsx`, `BookmapHeatmapPanel.tsx`, `PriceChartOverlay.tsx`, `TradeHistoryPanel.tsx`.
- **Account/execution**: `AccountSummaryPanel.tsx`, `PositionsPanel.tsx`, `OpenOrdersPanel.tsx`, `OrderHistoryPanel.tsx`, `AssetsPanel.tsx`, `ExecutionReportPanel.tsx`.
- **Signals/evidence**: `SignalPreviewPanel.tsx`, `GateDecisionPanel.tsx`, `TradeActionEvidencePanel.tsx`, `QuantLevelsPanel.tsx`, `TickToTradeLatencyPanel.tsx`.
- **Health/status**: `RuntimeHealthPanel.tsx`, `FreshnessBadge.tsx`, `StatusChip.tsx`, `HashPill.tsx`.

## Conventions
- Panels read state via selectors from `lib/tradehud/selectors.ts` and formatters from `lib/tradehud/{number,time}-format.ts`. Never parse raw events in a panel.
- Use Ant Design primitives; no new UI library.
- Panel text must reinforce authority limits: draft-only, advisory-only, observational-only.
- Colocated tests (`*.test.tsx`) run under Vitest/jsdom.

## Anti-patterns (THIS PROJECT)
- Never place orders, expose credentials, or call `submit_order`/`TradeAction` from a panel.
- Never fetch directly — data comes through the feed + reducer; panels are display-only.
- Never drift TS types away from `lib/tradehud/types.ts` (mirror of `packages/tradehud_contracts/models.py`).
- Never treat these panels as runtime authority — they display backend/ND state only.

## Verification
```bash
cd apps/web && npx vitest run components/tradehud
cd apps/web && npx playwright test e2e/tradehud.spec.ts
```
