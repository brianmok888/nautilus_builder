"use client";

import type { FillEvent } from "../../lib/tradehud/types";
import { fmtPrice, fmtQty } from "../../lib/tradehud/number-format";
import { fmtTime } from "../../lib/tradehud/time-format";

export function TradeHistoryPanel({ fills }: { fills: FillEvent[] }) {
  // Newest first, capped at 30 rows.
  const rows = [...fills]
    .sort((a, b) => b.ts_event_ns - a.ts_event_ns)
    .slice(0, 30);

  return (
    <div className="tradehud-panel">
      <div className="tradehud-panel-header">
        <span className="tradehud-panel-title">Trade History</span>
        {fills.length > 0 && (
          <span className="tradehud-panel-badge tradehud-panel-badge-info">
            {fills.length}
          </span>
        )}
      </div>
      <div className="tradehud-panel-body">
        {rows.length === 0 ? (
          <div className="tradehud-muted">No fills</div>
        ) : (
          <table className="tradehud-table">
            <thead>
              <tr>
                <th>Time</th>
                <th>Symbol</th>
                <th>Side</th>
                <th>Price</th>
                <th>Qty</th>
                <th>Fee</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((f) => (
                <tr key={f.fill_id}>
                  <td>{fmtTime(f.ts_event_ns)}</td>
                  <td>{f.symbol}</td>
                  <td className={f.side === "buy" ? "tradehud-pos" : "tradehud-neg"}>
                    {f.side}
                  </td>
                  <td className="tradehud-td-right">{fmtPrice(f.price)}</td>
                  <td className="tradehud-td-right">{fmtQty(f.qty)}</td>
                  <td className="tradehud-td-right tradehud-neg">{fmtPrice(f.fee)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
