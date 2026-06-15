"use client";

import type { GateDecision } from "../../lib/tradehud/types";
import { fmtPrice, fmtSigned } from "../../lib/tradehud/number-format";
import { FreshnessBadge } from "./FreshnessBadge";
import { StatusChip } from "./StatusChip";
import { HashPill } from "./HashPill";

export function GateDecisionPanel({ gate }: { gate: GateDecision | null }) {
  return (
    <div className="tradehud-panel">
      <div className="tradehud-panel-header">
        <span className="tradehud-panel-title">Gate Decision</span>
        {gate && <FreshnessBadge meta={gate} />}
      </div>
      <div className="tradehud-panel-body">
        {!gate ? (
          <div className="tradehud-missing-text">GATE DECISION MISSING</div>
        ) : (
          <>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
              <StatusChip status={gate.decision} />
              <span className="tradehud-evidence-label tradehud-evidence-runtime">
                APPROVAL EVIDENCE
              </span>
            </div>
            <table className="tradehud-table">
              <tbody>
                <tr>
                  <td className="tradehud-muted">Decision</td>
                  <td className="tradehud-td-right">
                    <StatusChip status={gate.decision} />
                  </td>
                </tr>
                <tr>
                  <td className="tradehud-muted">Blocking Gate</td>
                  <td className="tradehud-td-right">
                    {gate.first_blocking_gate ? (
                      <span className="tradehud-neg">{gate.first_blocking_gate}</span>
                    ) : (
                      <span className="tradehud-pos">none</span>
                    )}
                  </td>
                </tr>
                <tr>
                  <td className="tradehud-muted">Reason Code</td>
                  <td className="tradehud-td-right tradehud-amber">{gate.reason_code}</td>
                </tr>
                <tr>
                  <td className="tradehud-muted">Conf Δ</td>
                  <td className="tradehud-td-right">
                    <span className={gate.confidence_delta >= 0 ? "tradehud-pos" : "tradehud-neg"}>
                      {fmtSigned(gate.confidence_delta, 4)}
                    </span>
                  </td>
                </tr>
                <tr>
                  <td className="tradehud-muted">Size Mod</td>
                  <td className="tradehud-td-right">{(gate.size_modifier * 100).toFixed(1)}%</td>
                </tr>
                <tr>
                  <td className="tradehud-muted">Target</td>
                  <td className="tradehud-td-right">{fmtPrice(gate.target_hint)}</td>
                </tr>
              </tbody>
            </table>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 3, marginTop: 6 }}>
              <HashPill hash={gate.gate_decision_hash} label="gate" />
              <HashPill hash={gate.source_signal_hash} label="sig" />
            </div>
          </>
        )}
      </div>
    </div>
  );
}
