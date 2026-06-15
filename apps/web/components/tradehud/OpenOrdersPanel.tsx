"use client";

import type { OpenOrderSnapshot } from "../../lib/tradehud/types";
import { fmtPrice, fmtQty } from "../../lib/tradehud/number-format";
import { StatusChip } from "./StatusChip";

export function OpenOrdersPanel({ orders }: { orders: OpenOrderSnapshot[] }) {
  return (
    <div className="tradehud-panel">
      <div className="tradehud-panel-header">
        <span className="tradehud-panel-title">Open Orders</span>
        {orders.length > 0 && (
          <span className="tradehud-panel-badge tradehud-panel-badge-info">
            {orders.length}
          </span>
        )}
      </div>
      <div className="tradehud-panel-body">
        {orders.length === 0 ? (
          <div className="tradehud-muted">No open orders</div>
        ) : (
          <table className="tradehud-table">
            <thead>
              <tr>
                <th>Symbol</th>
                <th>Side</th>
                <th>Type</th>
                <th>Price</th>
                <th>Qty</th>
                <th>Filled</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {orders.map((o) => (
                <tr key={o.order_id}>
                  <td>{o.symbol}</td>
                  <td className={o.side === "buy" ? "tradehud-pos" : "tradehud-neg"}>
                    {o.side}
                  </td>
                  <td>{o.order_type}</td>
                  <td className="tradehud-td-right">{fmtPrice(o.price)}</td>
                  <td className="tradehud-td-right">{fmtQty(o.qty)}</td>
                  <td className="tradehud-td-right">{fmtQty(o.filled_qty)}</td>
                  <td>
                    <StatusChip status={o.status} />
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
