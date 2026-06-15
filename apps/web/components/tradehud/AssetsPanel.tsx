"use client";

import React from "react";
import type { AssetSnapshot } from "../../lib/tradehud/types";
import { fmtQty, fmtNotional } from "../../lib/tradehud/number-format";

interface AssetsPanelProps {
  assets: AssetSnapshot[];
}

export const AssetsPanel: React.FC<AssetsPanelProps> = ({ assets }) => {
  const rows = assets ?? [];

  return (
    <section className="tradehud-panel">
      <header className="tradehud-panel-header">
        <span className="tradehud-panel-title">Assets</span>
        <span className="tradehud-panel-badge tradehud-panel-badge-info">
          {rows.length}
        </span>
      </header>
      <div className="tradehud-panel-body">
        {rows.length === 0 ? (
          <div className="tradehud-muted">No assets</div>
        ) : (
          <table className="tradehud-table">
            <thead>
              <tr>
                <th>Asset</th>
                <th className="tradehud-td-right">Free</th>
                <th className="tradehud-td-right">Locked</th>
                <th className="tradehud-td-right">USD Value</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((a, i) => (
                <tr key={`${a.asset}-${i}`}>
                  <td>{a.asset}</td>
                  <td className="tradehud-td-right">{fmtQty(a.free)}</td>
                  <td className="tradehud-td-right">{fmtQty(a.locked)}</td>
                  <td className="tradehud-td-right tradehud-cyan">
                    {fmtNotional(a.usd_value)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </section>
  );
};

export default AssetsPanel;
