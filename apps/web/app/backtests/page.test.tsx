import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import BacktestsPage from "./page";

vi.mock("../../components/dashboard/BuilderDashboard", () => ({
  BuilderDashboard: ({ initialTab }: { readonly initialTab?: string }) => (
    <div data-testid="dashboard-initial-tab">{initialTab}</div>
  ),
}));

describe("BacktestsPage", () => {
  it("renders the Backtest Center dashboard lane at /backtests", () => {
    render(<BacktestsPage />);

    expect(screen.getByTestId("dashboard-initial-tab")).toHaveTextContent("backtest");
  });
});
