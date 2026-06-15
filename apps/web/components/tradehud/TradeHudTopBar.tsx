"use client";

import type { TradeHudState } from "../../lib/tradehud/types";
import { fmtPrice, fmtBps } from "../../lib/tradehud/number-format";
import { fmtLatency } from "../../lib/tradehud/time-format";

export function TradeHudTopBar({ state }: { state: TradeHudState }) {
  const book = state.bookTop;
  const latency = state.tickToTrade;

  return (
    <div className="tradehud-topbar">
      <div className="tradehud-topbar-section">
        <span className="tradehud-topbar-label">Venue</span>
        <span className="tradehud-topbar-value">{state.selectedVenue}</span>
      </div>
      <div className="tradehud-topbar-sep" />
      <div className="tradehud-topbar-section">
        <span className="tradehud-topbar-label">Symbol</span>
        <span className="tradehud-topbar-value tradehud-cyan">{state.selectedSymbol}</span>
      </div>
      <div className="tradehud-topbar-sep" />
      <div className="tradehud-topbar-section">
        <span className="tradehud-topbar-label">Account</span>
        <span className="tradehud-topbar-value">{state.selectedAccount}</span>
      </div>
      <div className="tradehud-topbar-sep" />
      <div className="tradehud-topbar-section">
        <span className="tradehud-topbar-label">Mode</span>
        <span className="tradehud-topbar-value tradehud-amber">{state.mode.toUpperCase()}</span>
      </div>
      <div className="tradehud-topbar-sep" />
      <div className="tradehud-topbar-section">
        <span className="tradehud-topbar-label">Feed</span>
        <span className="tradehud-topbar-value">{state.feedMode.toUpperCase()}</span>
      </div>
      {book && (
        <>
          <div className="tradehud-topbar-sep" />
          <div className="tradehud-topbar-section">
            <span className="tradehud-topbar-label">Bid</span>
            <span className="tradehud-topbar-value tradehud-pos">{fmtPrice(book.bid_price, 1)}</span>
          </div>
          <div className="tradehud-topbar-section">
            <span className="tradehud-topbar-label">Ask</span>
            <span className="tradehud-topbar-value tradehud-neg">{fmtPrice(book.ask_price, 1)}</span>
          </div>
          <div className="tradehud-topbar-section">
            <span className="tradehud-topbar-label">Spread</span>
            <span className="tradehud-topbar-value">{fmtBps(book.spread_bps)}</span>
          </div>
        </>
      )}
      {latency && (
        <>
          <div className="tradehud-topbar-sep" />
          <div className="tradehud-topbar-section">
            <span className="tradehud-topbar-label">T2T</span>
            <span className="tradehud-topbar-value">{fmtLatency(latency.total_tick_to_trade_us)}</span>
          </div>
        </>
      )}
      <div className="tradehud-no-authority">
        ⚠ NO BROWSER ORDER AUTHORITY
      </div>
    </div>
  );
}
