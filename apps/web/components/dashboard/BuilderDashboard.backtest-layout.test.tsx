import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { BuilderDashboard } from "./BuilderDashboard";

vi.mock("next/navigation", () => ({
  useSearchParams: () => ({ get: () => null }),
  useRouter: () => ({ replace: vi.fn() }),
}));

const MOCK_STRATEGY = {
  strategy_id: "strat_validated_001",
  strategy_lineage_id: "line_alpha",
  status: "validated",
  latest_spec: {
    adapter_id: "BINANCE_PERP",
    instrument_id: "BTCUSDT-PERP",
    data_range: "2024-01-01:2024-03-01",
    data_type: "historical_bars",
    bar_type: "BTCUSDT-PERP.BINANCE-1-MINUTE-LAST-EXTERNAL",
  },
};

function mockApiResponses(withStrategy = false) {
  const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
    const url = String(input);
    if (url === "/api/strategies")
      return Response.json(withStrategy ? [MOCK_STRATEGY] : []);
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

describe("BuilderDashboard Backtest Center layout", () => {
  afterEach(() => vi.restoreAllMocks());

  it("renders full 4-step top-down workflow order when a strategy is selected", async () => {
    mockApiResponses(true);
    const { container } = render(<BuilderDashboard initialTab="backtest" />);

    // Wait for the table to load with the mock strategy
    await waitFor(() => {
      expect(screen.getByText("strat_validated_001")).toBeInTheDocument();
    });

    // Click "Select" on the strategy row to trigger Selected Validated Strategy
    const selectButton = screen.getByRole("button", { name: /Select/i });
    fireEvent.click(selectButton);

    // Wait for Selected Validated Strategy to appear
    await waitFor(() => {
      expect(screen.getByText("Selected Validated Strategy")).toBeInTheDocument();
    });

    // Verify all 4 steps are present
    expect(screen.getByText("BacktestNode Replay")).toBeInTheDocument();
    expect(screen.getByText("Manual Promotion Review")).toBeInTheDocument();

    // Verify DOM text order: Strategies < Selected Validated Strategy < BacktestNode Replay < Manual Promotion Review
    const text = container.textContent ?? "";

    const strategiesIndex = text.indexOf("Strategies");
    const selectedIndex = text.indexOf("Selected Validated Strategy");
    const replayIndex = text.indexOf("BacktestNode Replay");
    const promotionIndex = text.indexOf("Manual Promotion Review");

    expect(strategiesIndex).toBeGreaterThanOrEqual(0);
    expect(selectedIndex).toBeGreaterThan(strategiesIndex);
    expect(replayIndex).toBeGreaterThan(selectedIndex);
    expect(promotionIndex).toBeGreaterThan(replayIndex);
  });
});
