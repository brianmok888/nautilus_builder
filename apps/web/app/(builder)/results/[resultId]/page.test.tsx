import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import ResultPage from "./page";

const fetchResultSummary = vi.fn();

vi.mock("../../../../lib/api", () => ({
  fetchResultSummary: (...args: unknown[]) => fetchResultSummary(...args),
}));

describe("ResultPage", () => {
  it("loads result payload from the backend contract before rendering dashboard sections", async () => {
    fetchResultSummary.mockResolvedValue({
      result_id: "result-42",
      metrics: { pnl: 12.5 },
      artifacts: { report: "db_data/reports/result-42.json" },
      trades: [{ symbol: "BTCUSDT", qty: 1 }],
      fills: [{ price: 100 }],
      logs: [{ message: "completed" }],
    });

    render(await ResultPage({ params: Promise.resolve({ resultId: "result-42" }) }));

    expect(fetchResultSummary).toHaveBeenCalledWith("result-42");
    // Metric title rendered
    expect(screen.getByText("pnl")).toBeTruthy();
    // Statistic splits 12.5 into "12" and ".5000"
    expect(screen.getByText(".5000")).toBeTruthy();
    // Artifacts in Descriptions
    expect(screen.getByText("report")).toBeTruthy();
    expect(screen.getByText("db_data/reports/result-42.json")).toBeTruthy();
    // Trades table
    expect(screen.getByText("BTCUSDT")).toBeTruthy();
  });
});
