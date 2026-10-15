# TradeHUD panel knowledge base

## OVERVIEW
Observational market, account and evidence panels mounted by TradeHudShell; retained domain, score 7.

## WHERE TO LOOK
| Task | Files | Role |
|---|---|---|
| Mount point | ../../app/tradehud/page.tsx | TradeHUD route |
| Feed and state wiring | TradeHudShell.tsx | Feed lifecycle and reducer |
| Layout/status | TradeHudTopBar.tsx, TradeTape.tsx, LaneHealthStrip.tsx | Shared display chrome |
| Market depth | OrderBookLadder.tsx, BookmapHeatmapPanel.tsx | Depth visualization |
| Price/trades | PriceChartOverlay.tsx, TradeHistoryPanel.tsx | Market history |
| Account | AccountSummaryPanel.tsx, PositionsPanel.tsx, AssetsPanel.tsx | Observed balances/positions |
| Orders | OpenOrdersPanel.tsx, OrderHistoryPanel.tsx, ExecutionReportPanel.tsx | Reported state |
| Decision evidence | SignalPreviewPanel.tsx, GateDecisionPanel.tsx, TradeActionEvidencePanel.tsx | Intent and gate context |
| Quant/latency | QuantLevelsPanel.tsx, TickToTradeLatencyPanel.tsx | Runtime context |
| Health badges | RuntimeHealthPanel.tsx, FreshnessBadge.tsx, StatusChip.tsx | Source status |

## CONVENTIONS
- Read state through lib/tradehud selectors and shared formatters.
- Keep raw event parsing and network transport out of individual panels.
- Colocated .test.tsx checks run with Vitest/jsdom.
- Keep evidence labels distinct from execution reports and account snapshots.
- Test the panel slice with npm run test -- components/tradehud from apps/web.
- Browser coverage is in e2e/tradehud.spec.ts under the separate Playwright runner.

## ANTI-PATTERNS
- Do not place orders or expose credentials through an observational panel.
- Do not show a missing metric as zero or infer a fill from trade-action intent.
- Do not fetch per panel or drift from the shared TradeHUD event types.
