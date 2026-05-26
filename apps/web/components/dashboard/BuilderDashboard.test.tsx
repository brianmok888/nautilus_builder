import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { BuilderDashboard } from "./BuilderDashboard";

describe("BuilderDashboard", () => {
  it("renders the command-center workflow with a prompt-first entry point", () => {
    render(<BuilderDashboard />);

    expect(screen.getByText("Command center")).toBeInTheDocument();
    expect(screen.getByText("Describe strategy")).toBeInTheDocument();
    expect(screen.getByText("AI → StrategySpec → Market data → Backtest → Review → Execution Lane")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Start drafting" })).toBeInTheDocument();
    expect(screen.getByText("Execution lane status")).toBeInTheDocument();
    expect(screen.queryByText(/submit_order/i)).not.toBeInTheDocument();
  });
});
