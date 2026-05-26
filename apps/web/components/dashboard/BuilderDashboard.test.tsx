import { fireEvent, render, screen } from "@testing-library/react";
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

  it("uses CTA buttons to move between compact workflow sections", () => {
    render(<BuilderDashboard />);

    fireEvent.click(screen.getByRole("button", { name: "Continue to market setup" }));
    expect(screen.getByRole("tab", { name: "2. StrategySpec" })).toHaveAttribute("aria-selected", "true");
    expect(screen.getByText("Market context")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Start drafting" }));
    expect(screen.getByRole("tab", { name: "1. AI prompt" })).toHaveAttribute("aria-selected", "true");
    expect(screen.getByLabelText("Strategy prompt")).toBeInTheDocument();
  });
});
