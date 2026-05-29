import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { BuilderDashboard } from "./BuilderDashboard";

vi.mock("next/navigation", () => ({
  useSearchParams: () => ({ get: () => null }),
  useRouter: () => ({ replace: vi.fn() }),
}));

function mockApiResponses() {
  const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
    const url = String(input);
    if (url === "/api/strategies") return Response.json([]);
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

  it("renders Strategy Builder as default active lane", () => {
    mockApiResponses();
    render(<BuilderDashboard />);

    // 1-2-3 flow buttons visible
    expect(screen.getByText(/Strategy Builder/)).toBeInTheDocument();
    expect(screen.getByText(/Backtest Center/)).toBeInTheDocument();
    expect(screen.getByText(/Execution Lane/)).toBeInTheDocument();

    // Strategy builder tab shows strategy table header
    expect(screen.getByText("Strategies")).toBeInTheDocument();
    // Shows AI copilot section
    expect(screen.getByText("Strategy Editor")).toBeInTheDocument();
  });

  it("switches to Backtest Center lane on button click", async () => {
    mockApiResponses();
    render(<BuilderDashboard />);

    // Click Backtest Center button
    const backtestButtons = screen.getAllByText(/Backtest Center/);
    fireEvent.click(backtestButtons[0].closest("button")!);

    await waitFor(() => {
      expect(screen.getByText("BacktestNode Replay")).toBeInTheDocument();
      expect(screen.getByText("Manual Promotion Review")).toBeInTheDocument();
    });
  });

  it("switches to Execution Lane on button click", async () => {
    mockApiResponses();
    render(<BuilderDashboard />);

    const executionButtons = screen.getAllByText(/Execution Lane/);
    fireEvent.click(executionButtons[0].closest("button")!);

    await waitFor(() => {
      expect(screen.getByText("Approved Strategies")).toBeInTheDocument();
    });
  });

  it("keeps manual promotion inside Backtest Center, not Strategy Builder", () => {
    mockApiResponses();
    render(<BuilderDashboard />);

    // Strategy Builder tab should NOT show promotion
    expect(screen.queryByText("Manual Promotion Review")).not.toBeInTheDocument();
    expect(screen.queryByText("Manual promotion review")).not.toBeInTheDocument();
  });
});
