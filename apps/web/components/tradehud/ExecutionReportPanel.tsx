"use client";

import type { ExecutionReport } from "../../lib/tradehud/types";
import { fmtPrice, fmtQty } from "../../lib/tradehud/number-format";
import { fmtTime, fmtLatency } from "../../lib/tradehud/time-format";
import { FreshnessBadge } from "./FreshnessBadge";
import { StatusChip } from "./StatusChip";
import { HashPill } from "./HashPill";

export function ExecutionReportPanel({ report }: { report: ExecutionReport | null }) {
  return (
    <div className="tradehud-panel">
      <div className="tradehud-panel-header">
        <span className="tradehud-panel-title">Execution Report</span>
        {report && <FreshnessBadge meta={report} />}
      </div>
      <div className="tradehud-panel-body">
        {!report ? (
          <div className="tradehud-muted" style={{ padding: 12, textAlign: "center" }}>
            No execution report from runtime
          </div>
        ) : (
          <>
            <div style={{ marginBottom: 6 }}>
              <span className="tradehud-evidence-label tradehud-evidence-exchange">
                EXCHANGE/RUNTIME EVIDENCE
              </span>
            </div>
            <table className="tradehud-table">
              <tbody>
                <tr>
                  <td className="tradehud-muted">Status</td>
                  <td className="tradehud-td-right"><StatusChip status={report.status} /></td>
                </tr>
                <tr>
                  <td className="tradehud-muted">Symbol</td>
                  <td className="tradehud-td-right">{report.symbol}</td>
                </tr>
                <tr>
                  <td className="tradehud-muted">Side</td>
                  <td className="tradehud-td-right">
                    <span className={report.side === "buy" ? "tradehud-pos" : "tradehud-neg"}>
                      {report.side.toUpperCase()}
                    </span>
                  </td>
                </tr>
                <tr>
                  <td className="tradehud-muted">Filled</td>
                  <td className="tradehud-td-right">{fmtQty(report.filled_qty)}</td>
                </tr>
                <tr>
                  <td className="tradehud-muted">Avg Price</td>
                  <td className="tradehud-td-right">{fmtPrice(report.avg_fill_price)}</td>
                </tr>
                <tr>
                  <td className="tradehud-muted">Exch Order ID</td>
                  <td className="tradehud-td-right tradehud-cyan">{report.exchange_order_id ?? "—"}</td>
                </tr>
                <tr>
                  <td className="tradehud-muted">Client Order ID</td>
                  <td className="tradehud-td-right">{report.client_order_id}</td>
                </tr>
                {report.submit_to_ack_us != null && (
                  <tr>
                    <td className="tradehud-muted">Submit→Ack</td>
                    <td className="tradehud-td-right">{fmtLatency(report.submit_to_ack_us)}</td>
                  </tr>
                )}
                {report.ack_to_fill_us != null && (
                  <tr>
                    <td className="tradehud-muted">Ack→Fill</td>
                    <td className="tradehud-td-right">{fmtLatency(report.ack_to_fill_us)}</td>
                  </tr>
                )}
                {report.rejection_reason && (
                  <tr>
                    <td className="tradehud-muted">Rejection</td>
                    <td className="tradehud-td-right tradehud-neg">{report.rejection_reason}</td>
                  </tr>
                )}
              </tbody>
            </table>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 3, marginTop: 6 }}>
              <HashPill hash={report.trade_action_hash} label="ta" />
            </div>
          </>
        )}
      </div>
    </div>
  );
}
