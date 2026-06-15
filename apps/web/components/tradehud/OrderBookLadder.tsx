"use client";

import React from "react";
import type { MarketBookL2 } from "../../lib/tradehud/types";
import { fmtPrice, fmtQty, fmtBps, fmtAge } from "../../lib/tradehud/number-format";

interface OrderBookLadderProps {
  bookL2: MarketBookL2 | null;
}

const MAX_LEVELS = 12;

export const OrderBookLadder: React.FC<OrderBookLadderProps> = ({ bookL2 }) => {
  const missing =
    !bookL2 || (bookL2 as any).missing === true || (bookL2 as any).source_available === false;

  if (missing || !bookL2) {
    return (
      <section className="tradehud-panel">
        <header className="tradehud-panel-header">
          <span className="tradehud-panel-title">Order Book</span>
        </header>
        <div className="tradehud-panel-body">
          <div className="tradehud-missing-text">Order book unavailable</div>
        </div>
      </section>
    );
  }

  const asks = (bookL2.asks ?? []).slice(0, MAX_LEVELS);
  const bids = (bookL2.bids ?? []).slice(0, MAX_LEVELS);

  // Largest total across visible levels for depth bar scaling
  const maxTotal = Math.max(
    1,
    ...asks.map((l) => l.total || 0),
    ...bids.map((l) => l.total || 0),
  );

  // Asks rendered top->bottom from worst (highest) to best (lowest), so the
  // best ask sits directly above the mid summary row.
  const asksDesc = [...asks].reverse();

  return (
    <section className="tradehud-panel">
      <header className="tradehud-panel-header">
        <span className="tradehud-panel-title">Order Book</span>
        <span className="tradehud-panel-badge tradehud-panel-badge-info">
          {bookL2.symbol}
        </span>
      </header>
      <div className="tradehud-panel-body">
        <table className="tradehud-table">
          <thead>
            <tr>
              <th>Price</th>
              <th className="tradehud-td-right">Size</th>
              <th className="tradehud-td-right">Total</th>
              <th className="tradehud-td-right">Age</th>
              <th>Source</th>
            </tr>
          </thead>
          <tbody>
            {asksDesc.map((lvl, i) => (
              <tr
                key={`ask-${i}`}
                className="tradehud-ob-row tradehud-ob-row-ask"
                style={{
                  backgroundSize: `${((lvl.total || 0) / maxTotal) * 100}% 100%`,
                }}
              >
                <td className="tradehud-neg">{fmtPrice(lvl.price)}</td>
                <td className="tradehud-td-right">{fmtQty(lvl.size)}</td>
                <td className="tradehud-td-right">{fmtQty(lvl.total)}</td>
                <td className="tradehud-td-right tradehud-muted">{fmtAge(lvl.age_ms)}</td>
                <td className="tradehud-muted">{lvl.source}</td>
              </tr>
            ))}

            <tr className="tradehud-ob-summary">
              <td>
                Spread{" "}
                <span className="tradehud-amber">{fmtBps(bookL2.spread_bps)}</span>
              </td>
              <td className="tradehud-td-right">
                Imb{" "}
                <span
                  className={
                    bookL2.top5_imbalance >= 0 ? "tradehud-pos" : "tradehud-neg"
                  }
                >
                  {(bookL2.top5_imbalance * 100).toFixed(1)}%
                </span>
              </td>
              <td className="tradehud-td-right" colSpan={3}>
                Mid <span className="tradehud-cyan">{fmtPrice(bookL2.microprice)}</span>
              </td>
            </tr>

            {bids.map((lvl, i) => (
              <tr
                key={`bid-${i}`}
                className="tradehud-ob-row tradehud-ob-row-bid"
                style={{
                  backgroundSize: `${((lvl.total || 0) / maxTotal) * 100}% 100%`,
                }}
              >
                <td className="tradehud-pos">{fmtPrice(lvl.price)}</td>
                <td className="tradehud-td-right">{fmtQty(lvl.size)}</td>
                <td className="tradehud-td-right">{fmtQty(lvl.total)}</td>
                <td className="tradehud-td-right tradehud-muted">{fmtAge(lvl.age_ms)}</td>
                <td className="tradehud-muted">{lvl.source}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
};

export default OrderBookLadder;
