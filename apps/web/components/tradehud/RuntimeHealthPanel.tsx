"use client";

import type { RuntimeHealth, LaneHealth } from "../../lib/tradehud/types";
import { fmtAge } from "../../lib/tradehud/number-format";

type LaneKey =
  | "run_main_strategy_signal"
  | "run_gate_engine"
  | "run_execution_lane"
  | "ai_lane_advisory"
  | "data_health";

const LANES: { key: LaneKey; label: string }[] = [
  { key: "run_main_strategy_signal", label: "Strategy Signal" },
  { key: "run_gate_engine", label: "Gate Engine" },
  { key: "run_execution_lane", label: "Execution Lane" },
  { key: "ai_lane_advisory", label: "AI Advisory" },
  { key: "data_health", label: "Data Health" },
];

export function RuntimeHealthPanel({
  health,
}: {
  health: RuntimeHealth | null;
}) {
  return (
    <div className="tradehud-panel">
      <div className="tradehud-panel-header">
        <span className="tradehud-panel-title">Runtime Health</span>
        {health && (
          <span
            className={`tradehud-panel-badge ${
              health.stale
                ? "tradehud-panel-badge-warn"
                : "tradehud-panel-badge-success"
            }`}
          >
            {health.stale ? "stale" : "live"}
          </span>
        )}
      </div>
      <div className="tradehud-panel-body">
        {!health ? (
          <div className="tradehud-missing-text">Runtime health unavailable</div>
        ) : (
          <>
            {LANES.map(({ key, label }) => {
              const lane: LaneHealth = health[key];
              return (
                <div className="tradehud-kv" key={key}>
                  <span className="tradehud-kv-key">
                    <span
                      className={`tradehud-lane-dot tradehud-lane-dot-${lane.status}`}
                    />{" "}
                    {label}
                  </span>
                  <span className="tradehud-kv-val">
                    <span className="tradehud-muted">
                      {lane.age_ms != null ? fmtAge(lane.age_ms) : "—"}
                    </span>
                    {lane.reason_code && (
                      <span className="tradehud-amber"> · {lane.reason_code}</span>
                    )}
                  </span>
                </div>
              );
            })}
          </>
        )}
      </div>
    </div>
  );
}
