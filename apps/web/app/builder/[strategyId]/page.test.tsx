import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

vi.mock("next/navigation", () => ({
  useSearchParams: () => ({ get: () => null }),
  useRouter: () => ({ replace: vi.fn() }),
}));

vi.mock("../../../lib/api", () => ({
  fetchStrategies: () => Promise.resolve([]),
  fetchExecutionLaneStatus: () => Promise.resolve({
    mode: "execution_lane",
    runtime_profile_id: null,
    profiles: 0,
    queued_commands: 0,
    claimed_commands: 0,
    reported_commands: 0,
    reports: 0,
    sessions: 0,
    running_sessions: 0,
    venue_bindings: [],
    ui_features: {
      execution_lane_ui_enabled: false,
      paper_controls_enabled: false,
      live_controls_enabled: false,
      credential_inputs_allowed: false,
      strategy_lane_coupled: false,
    },
    strategy_lane_coupled: false,
    may_submit_order: false,
  }),
}));

import BuilderStrategyPage from "./page";

describe("BuilderStrategyPage", () => {
  it("renders builder workspace for the given strategy", async () => {
    render(await BuilderStrategyPage({ params: Promise.resolve({ strategyId: "strategy_001" }) }));

    expect(screen.getByText(/strategy_001/)).toBeInTheDocument();
    expect(screen.getByText("Strategy Editor")).toBeInTheDocument();
  });
});
