"use client";

import type { TickToTradeTrace } from "../../lib/tradehud/types";
import { fmtLatency } from "../../lib/tradehud/time-format";

export function TickToTradeLatencyPanel({
  trace,
}: {
  trace: TickToTradeTrace | null;
}) {
  return (
    <div className="tradehud-panel">
      <div className="tradehud-panel-header">
        <span className="tradehud-panel-title">Tick→Trade Latency</span>
        {trace && (
          <span className="tradehud-panel-badge tradehud-panel-badge-success">
            {fmtLatency(trace.total_tick_to_trade_us)}
          </span>
        )}
      </div>
      <div className="tradehud-panel-body">
        {!trace ? (
          <div className="tradehud-missing-text">Latency trace unavailable</div>
        ) : (
          <>
            <div className="tradehud-kv">
              <span className="tradehud-kv-key">Tick→Signal</span>
              <span className="tradehud-kv-val">
                {fmtLatency(trace.tick_to_signal_us)}
              </span>
            </div>
            <div className="tradehud-kv">
              <span className="tradehud-kv-key">Signal→Gate</span>
              <span className="tradehud-kv-val">
                {fmtLatency(trace.signal_to_gate_us)}
              </span>
            </div>
            <div className="tradehud-kv">
              <span className="tradehud-kv-key">Gate→Execution</span>
              <span className="tradehud-kv-val">
                {fmtLatency(trace.gate_to_execution_us)}
              </span>
            </div>
            <div className="tradehud-kv">
              <span className="tradehud-kv-key">Total</span>
              <span
                className="tradehud-kv-val tradehud-cyan"
                style={{ fontWeight: 700 }}
              >
                {fmtLatency(trace.total_tick_to_trade_us)}
              </span>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
