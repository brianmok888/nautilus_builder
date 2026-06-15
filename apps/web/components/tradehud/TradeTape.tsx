"use client";

import React from "react";
import type { MarketTrade } from "../../lib/tradehud/types";
import { fmtPrice, fmtQty, fmtNotional } from "../../lib/tradehud/number-format";
import { fmtTime } from "../../lib/tradehud/time-format";

interface TradeTapeProps {
  trades: MarketTrade[];
}

const MAX_ROWS = 50;

export const TradeTape: React.FC<TradeTapeProps> = ({ trades }) => {
  // Newest first, capped at MAX_ROWS
  const rows = [...trades]
    .sort((a, b) => b.ts_event_ns - a.ts_event_ns)
    .slice(0, MAX_ROWS);

  return (
    <section className="tradehud-panel">
      <header className="tradehud-panel-header">
        <span className="tradehud-panel-title">Trade Tape</span>
        <span className="tradehud-panel-badge tradehud-panel-badge-info">
          {trades.length}
        </span>
      </header>
      <div className="tradehud-panel-body">
        {rows.length === 0 ? (
          <div className="tradehud-muted">No trades</div>
        ) : (
          <table className="tradehud-table">
            <thead>
              <tr>
                <th>Time</th>
                <th className="tradehud-td-right">Price</th>
                <th className="tradehud-td-right">Qty</th>
                <th className="tradehud-td-right">Notional</th>
                <th className="tradehud-td-center">Side</th>
                <th>Flags</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((t) => {
                const isBuy = t.side === "buy";
                return (
                  <tr key={t.trade_id}>
                    <td className="tradehud-muted">{fmtTime(t.ts_event_ns)}</td>
                    <td className={`tradehud-td-right ${isBuy ? "tradehud-pos" : "tradehud-neg"}`}>
                      {fmtPrice(t.price)}
                    </td>
                    <td className="tradehud-td-right">{fmtQty(t.qty)}</td>
                    <td className="tradehud-td-right">{fmtNotional(t.notional)}</td>
                    <td className="tradehud-td-center">
                      <span className={isBuy ? "tradehud-pos" : "tradehud-neg"}>
                        {isBuy ? "BUY" : "SELL"}
                      </span>
                    </td>
                    <td>
                      {t.is_large_trade && (
                        <span className="tradehud-panel-badge tradehud-panel-badge-warn">
                          LARGE
                        </span>
                      )}{" "}
                      {t.is_sweep && (
                        <span className="tradehud-panel-badge tradehud-panel-badge-danger">
                          SWEEP
                        </span>
                      )}{" "}
                      {t.is_liquidation && t.liq_side === "long_liq" && (
                        <span className="tradehud-panel-badge tradehud-panel-badge-danger">
                          LONG_LIQ
                        </span>
                      )}{" "}
                      {t.is_liquidation && t.liq_side === "short_liq" && (
                        <span className="tradehud-panel-badge tradehud-panel-badge-danger">
                          SHORT_LIQ
                        </span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </section>
  );
};

export default TradeTape;
