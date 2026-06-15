"use client";

import type { RuntimeHealth, LaneHealth } from "../../lib/tradehud/types";
import { fmtAge } from "../../lib/tradehud/number-format";

const LANE_LABELS: Record<string, string> = {
  run_main_strategy_signal: "Signal",
  run_gate_engine: "Gate",
  run_execution_lane: "Execution",
  ai_lane_advisory: "AI Advisory",
  data_health: "Data",
};

export function LaneHealthStrip({ health }: { health: RuntimeHealth | null }) {
  if (!health) {
    return (
      <div className="tradehud-lane-strip">
        <span className="tradehud-muted">Runtime health unavailable</span>
      </div>
    );
  }
  const lanes: LaneHealth[] = [
    health.run_main_strategy_signal,
    health.run_gate_engine,
    health.run_execution_lane,
    health.ai_lane_advisory,
    health.data_health,
  ];
  return (
    <div className="tradehud-lane-strip">
      {lanes.map((lane) => (
        <div key={lane.lane} className="tradehud-lane-item" title={`${lane.lane}: ${lane.reason_code ?? "ok"}`}>
          <span className={`tradehud-lane-dot tradehud-lane-dot-${lane.status}`} />
          <span className="tradehud-muted">{LANE_LABELS[lane.lane] ?? lane.lane}</span>
          <span className={lane.stale ? "tradehud-amber" : "tradehud-muted"}>
            {lane.age_ms != null ? fmtAge(lane.age_ms) : "—"}
          </span>
        </div>
      ))}
    </div>
  );
}
