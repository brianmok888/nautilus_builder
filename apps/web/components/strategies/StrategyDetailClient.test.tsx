import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { StrategyDetailClient } from "./StrategyDetailClient";

const pushMock = vi.hoisted(() => vi.fn());

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: pushMock }),
}));

afterEach(() => {
  vi.restoreAllMocks();
  pushMock.mockReset();
});

const mockDetail = {
  strategy_id: "demo_backtested",
  strategy_lineage_id: "lineage_demo_backtested",
  status: "backtested",
  versions: [
    {
      strategy_version_id: "demo_backtested_v001",
      spec: {
        adapter_id: "BINANCE_PERP",
        venue: "BINANCE",
        instrument_id: "BTCUSDT-PERP",
        bar_type: "BTCUSDT-PERP.BINANCE-5-MINUTE-LAST-EXTERNAL",
        stage: "testing",
        status: "backtested",
        indicators: {
          ema_fast: { type: "EMA", input: "close", period: 20 },
          rsi: { type: "RSI", input: "close", period: 14 },
        },
        rules: {
          long_entry: { all: [{ crossed_above: ["ema_fast", "ema_slow"] }], any: null },
        },
        risk: { position_size_pct: 0.05, stop_loss_pct: 0.012, take_profit_pct: 0.024, max_hold_bars: 48 },
        validation: { bar_close_only: true, no_lookahead_required: true },
        data_range: { start: "2025-01-01T00:00:00Z", end: "2025-06-01T00:00:00Z" },
        provenance: { created_by: "user" },
      },
    },
  ],
};

describe("StrategyDetailClient", () => {
  it("loads and renders strategy detail with overview cards", async () => {
    vi.spyOn(await import("../../lib/api"), "fetchStrategyDetail").mockResolvedValueOnce(mockDetail);

    render(<StrategyDetailClient strategyId="demo_backtested" />);

    // Wait for data to load — check for a stable element
    await waitFor(() => {
      expect(screen.getByText("Overview")).toBeInTheDocument();
    });

    // Strategy ID is shown
    expect(screen.getAllByText(/demo_backtested/).length).toBeGreaterThan(0);
  });

  it("shows version history with version ID", async () => {
    vi.spyOn(await import("../../lib/api"), "fetchStrategyDetail").mockResolvedValueOnce(mockDetail);

    render(<StrategyDetailClient strategyId="demo_backtested" />);

    await waitFor(() => {
      expect(screen.getByText("Version History")).toBeInTheDocument();
    });
    expect(screen.getByText("demo_backtested_v001")).toBeInTheDocument();
  });

  it("disables Edit for backtested strategies, enables Clone", async () => {
    vi.spyOn(await import("../../lib/api"), "fetchStrategyDetail").mockResolvedValueOnce(mockDetail);

    render(<StrategyDetailClient strategyId="demo_backtested" />);

    await waitFor(() => {
      expect(screen.getByText("Actions")).toBeInTheDocument();
    });

    const editBtn = screen.getByText("Edit in Builder").closest("button")!;
    expect(editBtn.disabled).toBe(true);

    const cloneBtn = screen.getByText("Clone as Draft").closest("button")!;
    expect(cloneBtn.disabled).toBe(false);
  });

  it("routes Backtest action to the clean Backtest Center path", async () => {
    vi.spyOn(await import("../../lib/api"), "fetchStrategyDetail").mockResolvedValueOnce(mockDetail);

    render(<StrategyDetailClient strategyId="demo_backtested" />);

    await waitFor(() => {
      expect(screen.getByText("Actions")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("Backtest").closest("button")!);

    expect(pushMock).toHaveBeenCalledWith("/backtests");
  });
});
