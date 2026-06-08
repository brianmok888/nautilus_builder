import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { BuilderSafetyStatusPanel } from "./BuilderSafetyStatusPanel";

describe("BuilderSafetyStatusPanel", () => {
  it("renders safety status panel with no live order submission", () => {
    render(<BuilderSafetyStatusPanel />);
    // Title
    expect(screen.getByText("Builder safety status")).toBeDefined();
    // Safety items
    expect(screen.getAllByText("Execution authority").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Disabled").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Live credentials used").length).toBeGreaterThan(0);
    expect(screen.getAllByText("No").length).toBeGreaterThan(0);
    expect(screen.getAllByText("TradeAction generation").length).toBeGreaterThan(0);
    expect(screen.getAllByText("submit_order access").length).toBeGreaterThan(0);
    expect(screen.getAllByText("AI authority").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Advisory only").length).toBeGreaterThan(0);
  });

  it("shows Builder-only mode tag", () => {
    render(<BuilderSafetyStatusPanel />);
    expect(screen.getByText("Builder-only mode")).toBeDefined();
  });

  it("shows static guarantee text about live orders", () => {
    render(<BuilderSafetyStatusPanel />);
    // Text appears in subtitle and footer, so use getAllByText
    const matches = screen.getAllByText(/does not submit live orders/i);
    expect(matches.length).toBeGreaterThanOrEqual(1);
  });
});
