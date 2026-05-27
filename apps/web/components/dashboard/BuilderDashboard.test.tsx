import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { BuilderDashboard } from "./BuilderDashboard";

function mockStatusFetch() {
  const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
    const url = String(input);
    if (url === "/api/adapters") return Response.json([]);
    if (url.startsWith("/api/execution-lane/status")) {
      return Response.json({
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
      });
    }
    return Response.json({ error: `unexpected ${url}` }, { status: 404 });
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

describe("BuilderDashboard", () => {
  afterEach(() => vi.restoreAllMocks());

  it("renders the three-section operator workflow with Strategy Builder as entry point", () => {
    mockStatusFetch();
    render(<BuilderDashboard />);

    expect(screen.getByText("Command center")).toBeInTheDocument();
    expect(screen.getByText("Three-section operator workflow")).toBeInTheDocument();
    expect(screen.getAllByText("Strategy Builder → Backtest Center → Execution Lane").length).toBeGreaterThan(0);
    expect(screen.getByRole("button", { name: "Open Strategy Builder" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Run BacktestNode" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Open Execution Lane" })).toBeInTheDocument();
    expect(screen.getByText("Authority split")).toBeInTheDocument();
    expect(screen.queryByText(/submit_order/i)).not.toBeInTheDocument();
  });

  it("uses CTA buttons to move between the three compact workflow sections", async () => {
    mockStatusFetch();
    render(<BuilderDashboard />);

    expect(screen.getByRole("tab", { name: "1. Strategy Builder" })).toHaveAttribute("aria-selected", "true");
    expect(screen.getByLabelText("Strategy prompt")).toBeInTheDocument();
    expect(screen.getByText("Market context")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Run BacktestNode" }));
    expect(screen.getByRole("tab", { name: "2. Backtest Center" })).toHaveAttribute("aria-selected", "true");
    expect(screen.getByText("Validated run manifest")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Create backtest job" })).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Open Execution Lane" }));
    expect(screen.getByRole("tab", { name: "3. Execution Lane" })).toHaveAttribute("aria-selected", "true");
    await waitFor(() => expect(screen.getByText("Feature visibility matrix")).toBeInTheDocument());
  });

  it("keeps manual promotion inside Backtest Center instead of the strategy drafting lane", () => {
    mockStatusFetch();
    render(<BuilderDashboard />);

    expect(screen.queryByText("Manual promotion review")).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("tab", { name: "2. Backtest Center" }));
    expect(screen.getByText("Manual promotion review")).toBeInTheDocument();
    expect(screen.getByText("Safe promotion request")).toBeInTheDocument();
  });
});
