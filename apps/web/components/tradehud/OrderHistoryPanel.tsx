"use client";

import type { OrderEvent } from "../../lib/tradehud/types";
import { fmtPrice, fmtQty } from "../../lib/tradehud/number-format";
import { fmtTime } from "../../lib/tradehud/time-format";
import { StatusChip } from "./StatusChip";

export function OrderHistoryPanel({ events }: { events: OrderEvent[] }) {
  // Newest first, capped at 30 rows.
  const rows = [...events]
    .sort((a, b) => b.ts_event_ns - a.ts_event_ns)
    .slice(0, 30);

  return (
    <div className="tradehud-panel">
      <div className="tradehud-panel-header">
        <span className="tradehud-panel-title">Order History</span>
        {events.length > 0 && (
          <span className="tradehud-panel-badge tradehud-panel-badge-info">
            {events.length}
          </span>
        )}
      </div>
      <div className="tradehud-panel-body">
        {rows.length === 0 ? (
          <div className="tradehud-muted">No order events</div>
        ) : (
          <table className="tradehud-table">
            <thead>
              <tr>
                <th>Time</th>
                <th>Symbol</th>
                <th>Event</th>
                <th>Side</th>
                <th>Price</th>
                <th>Qty</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((e) => (
                <tr key={e.event_id}>
                  <td>{fmtTime(e.ts_event_ns)}</td>
                  <td>{e.symbol}</td>
                  <td>{e.event_type}</td>
                  <td className={e.side === "buy" ? "tradehud-pos" : "tradehud-neg"}>
                    {e.side}
                  </td>
                  <td className="tradehud-td-right">{fmtPrice(e.price)}</td>
                  <td className="tradehud-td-right">{fmtQty(e.qty)}</td>
                  <td>
                    <StatusChip status={e.status} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
