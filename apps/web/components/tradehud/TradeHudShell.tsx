"use client";

import { useReducer, useEffect, useRef } from "react";
import { createInitialState, reducer } from "../../lib/tradehud/reducer";
import { createFeed } from "../../lib/tradehud/replay-feed";
import { selectRecentTrades } from "../../lib/tradehud/selectors";
import type { TradeHudState } from "../../lib/tradehud/types";

import { TradeHudTopBar } from "./TradeHudTopBar";
import { LaneHealthStrip } from "./LaneHealthStrip";
import { BookmapHeatmapPanel } from "./BookmapHeatmapPanel";
import { OrderBookLadder } from "./OrderBookLadder";
import { TradeTape } from "./TradeTape";
import { SignalPreviewPanel } from "./SignalPreviewPanel";
import { GateDecisionPanel } from "./GateDecisionPanel";
import { TradeActionEvidencePanel } from "./TradeActionEvidencePanel";
import { ExecutionReportPanel } from "./ExecutionReportPanel";
import { QuantLevelsPanel } from "./QuantLevelsPanel";
import { TickToTradeLatencyPanel } from "./TickToTradeLatencyPanel";
import { RuntimeHealthPanel } from "./RuntimeHealthPanel";
import { PositionsPanel } from "./PositionsPanel";
import { AccountSummaryPanel } from "./AccountSummaryPanel";
import { AssetsPanel } from "./AssetsPanel";
import { OpenOrdersPanel } from "./OpenOrdersPanel";
import { OrderHistoryPanel } from "./OrderHistoryPanel";
import { TradeHistoryPanel } from "./TradeHistoryPanel";
import { PriceChartOverlay } from "./PriceChartOverlay";

import "./tradehud.css";

export function TradeHudShell() {
  const [state, dispatch] = useReducer(reducer, undefined, createInitialState);
  const feedRef = useRef<ReturnType<typeof createFeed> | null>(null);

  useEffect(() => {
    const feed = createFeed(state.selectedSymbol);
    feedRef.current = feed;
    feed.start(dispatch);
    return () => feed.stop();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const recentTrades = selectRecentTrades(state, 30);
  const bookStale = state.bookL2?.stale ?? true;
  const bookMissing = state.bookL2?.missing ?? (state.bookL2 === null);

  return (
    <div className="tradehud-root">
      <TradeHudTopBar state={state} />
      <LaneHealthStrip health={state.runtimeHealth} />
      {!state.backendAvailable && (
        <div className="tradehud-backend-warn">
          Backend unavailable — displaying local synthetic replay
        </div>
      )}

      {/* Main grid: heatmap | order book | trade tape */}
      <div className="tradehud-grid">
        <BookmapHeatmapPanel
          bookL2={state.bookL2}
          trades={recentTrades}
          signal={state.latestSignalPreview}
          gate={state.latestGateDecision}
          execution={state.latestExecutionReport}
          quantLevels={state.quantLevels}
          stale={bookStale}
          missing={bookMissing}
          sourceStatus={state.bookL2?.source_status ?? 'missing'}
        />
        <OrderBookLadder bookL2={state.bookL2} />
        <TradeTape trades={recentTrades} />
      </div>

      {/* Evidence row */}
      <div className="tradehud-grid-row-evidence" style={{ marginBottom: 4 }}>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr 1fr", gap: 4 }}>
          <SignalPreviewPanel signal={state.latestSignalPreview} />
          <GateDecisionPanel gate={state.latestGateDecision} />
          <TradeActionEvidencePanel action={state.latestTradeAction} />
          <ExecutionReportPanel report={state.latestExecutionReport} />
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 4 }}>
          <QuantLevelsPanel quant={state.quantLevels} />
          <TickToTradeLatencyPanel trace={state.tickToTrade} />
          <RuntimeHealthPanel health={state.runtimeHealth} />
        </div>
      </div>

      {/* Bottom row: positions | open orders | account/assets */}
      <div className="tradehud-grid-row-bottom" style={{ marginBottom: 4 }}>
        <PositionsPanel positions={state.positions} />
        <OpenOrdersPanel orders={state.openOrders} />
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 4 }}>
          <AccountSummaryPanel account={state.account} />
          <AssetsPanel assets={state.assets} />
        </div>
      </div>

      {/* History row */}
      <div className="tradehud-grid-row-evidence" style={{ marginBottom: 4 }}>
        <PriceChartOverlay bars={state.bars} />
        <OrderHistoryPanel events={state.orderHistory} />
      </div>
    </div>
  );
}
