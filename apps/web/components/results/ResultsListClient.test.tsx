import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ResultsListClient } from "./ResultsListClient";

const fetchResultList = vi.fn();

vi.mock("../../lib/api", () => ({
  fetchResultList: (...args: unknown[]) => fetchResultList(...args),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

describe("ResultsListClient", () => {
  it("loads and renders results in a table", async () => {
    fetchResultList.mockResolvedValue([
      {
        result_id: "res_001",
        strategy_lineage_id: "strat_alpha",
        strategy_version_id: "strat_alpha_v1",
        test_job_id: "job_001",
        metrics: { total_return: 0.15, sharpe: 1.8, max_drawdown: -0.04 },
        created_at: "res_001",
      },
    ]);

    render(<ResultsListClient />);

    await waitFor(() => {
      expect(screen.getByText("res_001")).toBeTruthy();
    });
    expect(screen.getByText("strat_alpha")).toBeTruthy();
    expect(screen.getByText("strat_alpha_v1")).toBeTruthy();
    expect(fetchResultList).toHaveBeenCalled();
  });

  it("shows empty state when no results", async () => {
    fetchResultList.mockResolvedValue([]);

    render(<ResultsListClient />);

    await waitFor(() => {
      expect(screen.getByText(/No backtest results yet/i)).toBeTruthy();
    });
  });

  it("shows error on fetch failure", async () => {
    fetchResultList.mockRejectedValue(new Error("API unavailable"));

    render(<ResultsListClient />);

    await waitFor(() => {
      expect(screen.getByText(/API unavailable/)).toBeTruthy();
    });
  });
});
