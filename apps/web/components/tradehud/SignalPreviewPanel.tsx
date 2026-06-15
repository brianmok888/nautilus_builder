"use client";

import type { StrategySignalPreview } from "../../lib/tradehud/types";
import { fmtPrice, fmtPct } from "../../lib/tradehud/number-format";
import { FreshnessBadge } from "./FreshnessBadge";
import { HashPill } from "./HashPill";

export function SignalPreviewPanel({ signal }: { signal: StrategySignalPreview | null }) {
  return (
    <div className="tradehud-panel">
      <div className="tradehud-panel-header">
        <span className="tradehud-panel-title">Strategy Signal Preview</span>
        {signal && <FreshnessBadge meta={signal} />}
      </div>
      <div className="tradehud-panel-body">
        {!signal ? (
          <div className="tradehud-missing-text">SIGNAL DATA MISSING</div>
        ) : (
          <>
            <div style={{ marginBottom: 6 }}>
              <span className="tradehud-evidence-label tradehud-evidence-not-executable">
                ⛔ NOT EXECUTABLE
              </span>
            </div>
            <table className="tradehud-table">
              <tbody>
                <tr>
                  <td className="tradehud-muted">Direction</td>
                  <td className="tradehud-td-right">
                    <span className={
                      signal.direction === "long" ? "tradehud-pos"
                      : signal.direction === "short" ? "tradehud-neg"
                      : "tradehud-muted"
                    }>
                      {signal.direction.toUpperCase()}
                    </span>
                  </td>
                </tr>
                <tr>
                  <td className="tradehud-muted">Confidence</td>
                  <td className="tradehud-td-right tradehud-cyan">{fmtPct(signal.confidence_score)}</td>
                </tr>
                <tr>
                  <td className="tradehud-muted">Target</td>
                  <td className="tradehud-td-right">{fmtPrice(signal.target_hint)}</td>
                </tr>
                <tr>
                  <td className="tradehud-muted">Invalidation</td>
                  <td className="tradehud-td-right">{fmtPrice(signal.invalidation_hint)}</td>
                </tr>
                <tr>
                  <td className="tradehud-muted">Size Hint</td>
                  <td className="tradehud-td-right">{signal.size_hint ?? "—"}</td>
                </tr>
              </tbody>
            </table>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 3, marginTop: 6 }}>
              <HashPill hash={signal.feature_hash} label="feat" />
              <HashPill hash={signal.context_hash} label="ctx" />
              <HashPill hash={signal.policy_hash} label="pol" />
              <HashPill hash={signal.graph_trace_hash} label="gtr" />
            </div>
          </>
        )}
      </div>
    </div>
  );
}
