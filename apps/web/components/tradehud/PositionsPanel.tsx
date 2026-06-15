"use client";

import React from "react";
import type { PositionSnapshot } from "../../lib/tradehud/types";
import { fmtPrice, fmtQty, fmtSigned, fmtNotional } from "../../lib/tradehud/number-format";

interface PositionsPanelProps {
  positions: PositionSnapshot[];
}

function sideClass(side: PositionSnapshot["side"]): string {
  switch (side) {
    case "long":
      return "tradehud-pos";
    case "short":
      return "tradehud-neg";
    default:
      return "tradehud-muted";
  }
}

export const PositionsPanel: React.FC<PositionsPanelProps> = ({ positions }) => {
  const rows = positions ?? [];

  return (
    <section className="tradehud-panel">
      <header className="tradehud-panel-header">
        <span className="tradehud-panel-title">Positions</span>
        <span className="tradehud-panel-badge tradehud-panel-badge-info">
          {rows.length}
        </span>
      </header>
      <div className="tradehud-panel-body">
        {rows.length === 0 ? (
          <div className="tradehud-muted">No open positions</div>
        ) : (
          <table className="tradehud-table">
            <thead>
              <tr>
                <th>Symbol</th>
                <th className="tradehud-td-center">Side</th>
                <th className="tradehud-td-right">Qty</th>
                <th className="tradehud-td-right">Entry</th>
                <th className="tradehud-td-right">Mark</th>
                <th className="tradehud-td-right">uPNL</th>
                <th className="tradehud-td-right">rPNL</th>
                <th className="tradehud-td-right">Margin</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((p, i) => (
                <tr key={`${p.symbol}-${p.venue}-${i}`}>
                  <td>
                    {p.symbol}
                    <span className="tradehud-muted"> {p.venue}</span>
                  </td>
                  <td className={`tradehud-td-center ${sideClass(p.side)}`}>
                    {p.side.toUpperCase()}
                  </td>
                  <td className="tradehud-td-right">{fmtQty(p.qty)}</td>
                  <td className="tradehud-td-right">{fmtPrice(p.entry_price)}</td>
                  <td className="tradehud-td-right">{fmtPrice(p.mark_price)}</td>
                  <td className={`tradehud-td-right ${p.unrealized_pnl >= 0 ? "tradehud-pos" : "tradehud-neg"}`}>
                    {fmtSigned(p.unrealized_pnl)}
                  </td>
                  <td className={`tradehud-td-right ${p.realized_pnl >= 0 ? "tradehud-pos" : "tradehud-neg"}`}>
                    {fmtSigned(p.realized_pnl)}
                  </td>
                  <td className="tradehud-td-right">{fmtNotional(p.margin)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </section>
  );
};

export default PositionsPanel;
