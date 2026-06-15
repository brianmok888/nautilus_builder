"use client";

import type { TradeActionEvidence } from "../../lib/tradehud/types";
import { fmtPrice, fmtQty } from "../../lib/tradehud/number-format";
import { fmtTime } from "../../lib/tradehud/time-format";
import { FreshnessBadge } from "./FreshnessBadge";
import { HashPill } from "./HashPill";

export function TradeActionEvidencePanel({ action }: { action: TradeActionEvidence | null }) {
  return (
    <div className="tradehud-panel">
      <div className="tradehud-panel-header">
        <span className="tradehud-panel-title">Trade Action Evidence</span>
        {action && <FreshnessBadge meta={action} />}
      </div>
      <div className="tradehud-panel-body">
        {!action ? (
          <div className="tradehud-muted" style={{ padding: 12, textAlign: "center" }}>
            No trade action evidence from runtime
          </div>
        ) : (
          <>
            <div style={{ marginBottom: 6 }}>
              <span className="tradehud-evidence-label tradehud-evidence-runtime">
                RUNTIME-CONSUMED EVIDENCE ONLY
              </span>
            </div>
            <table className="tradehud-table">
              <tbody>
                <tr>
                  <td className="tradehud-muted">Action</td>
                  <td className="tradehud-td-right">{action.action}</td>
                </tr>
                <tr>
                  <td className="tradehud-muted">Side</td>
                  <td className="tradehud-td-right">
                    <span className={action.side === "buy" ? "tradehud-pos" : "tradehud-neg"}>
                      {action.side.toUpperCase()}
                    </span>
                  </td>
                </tr>
                <tr>
                  <td className="tradehud-muted">Price</td>
                  <td className="tradehud-td-right">{fmtPrice(action.price)}</td>
                </tr>
                <tr>
                  <td className="tradehud-muted">Qty</td>
                  <td className="tradehud-td-right">{fmtQty(action.qty)}</td>
                </tr>
                <tr>
                  <td className="tradehud-muted">Created By</td>
                  <td className="tradehud-td-right tradehud-cyan">{action.created_by}</td>
                </tr>
                <tr>
                  <td className="tradehud-muted">Time</td>
                  <td className="tradehud-td-right">{fmtTime(action.ts_event_ns)}</td>
                </tr>
              </tbody>
            </table>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 3, marginTop: 6 }}>
              <HashPill hash={action.trade_action_hash} label="ta" />
              <HashPill hash={action.source_gate_decision_hash} label="gate" />
            </div>
          </>
        )}
      </div>
    </div>
  );
}
