"use client";

import type { QuantLevelsContext, QuantLevel } from "../../lib/tradehud/types";
import { fmtPrice } from "../../lib/tradehud/number-format";

/**
 * Maps a quant level kind to its semantic color class:
 *   resistance -> red (.tradehud-neg)
 *   support    -> green (.tradehud-pos)
 *   pivot      -> cyan (.tradehud-cyan)
 */
function levelColor(kind: QuantLevel["kind"]): string {
  switch (kind) {
    case "resistance":
      return "tradehud-neg";
    case "support":
      return "tradehud-pos";
    case "pivot":
      return "tradehud-cyan";
    default:
      return "tradehud-muted";
  }
}

export function QuantLevelsPanel({ quant }: { quant: QuantLevelsContext | null }) {
  return (
    <div className="tradehud-panel">
      <div className="tradehud-panel-header">
        <span className="tradehud-panel-title">Quant Levels</span>
        {quant && (
          <span className="tradehud-panel-badge tradehud-panel-badge-info">
            {quant.symbol}
          </span>
        )}
      </div>
      <div className="tradehud-panel-body">
        {!quant ? (
          <div className="tradehud-missing-text">Quant levels unavailable</div>
        ) : quant.levels.length === 0 ? (
          <div className="tradehud-muted">No levels</div>
        ) : (
          quant.levels.map((lvl) => {
            const color = levelColor(lvl.kind);
            return (
              <div className="tradehud-kv" key={lvl.label}>
                <span className="tradehud-kv-key">
                  <span className={`tradehud-evidence-label ${color}`}>
                    {lvl.kind}
                  </span>{" "}
                  {lvl.label}
                </span>
                <span className={`tradehud-kv-val ${color}`}>
                  {fmtPrice(lvl.price)}
                </span>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
