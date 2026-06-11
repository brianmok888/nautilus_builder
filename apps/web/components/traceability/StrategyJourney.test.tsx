import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import StrategyJourney from "./StrategyJourney";

const mockSteps = [
  { status: "completed" as const, label: "Draft StrategySpec", artifactId: "spec_001", hash: "a".repeat(64), actor: "operator" },
  { status: "completed" as const, label: "Validation", artifactId: "vr_001" },
  { status: "in_progress" as const, label: "Compile", artifactId: "compile_001" },
  { status: "blocked" as const, label: "Promotion", blockingReason: "BLOCK_EVIDENCE_MISSING: backtest_result required" },
  { status: "pending" as const, label: "Shadow Signal" },
];

describe("StrategyJourney", () => {
  it("renders all journey steps", () => {
    render(<StrategyJourney steps={mockSteps} strategyId="strat_001" />);
    expect(screen.getByText("Strategy Journey")).toBeTruthy();
    expect(screen.getByTestId("journey-step-Draft StrategySpec")).toBeTruthy();
    expect(screen.getByTestId("journey-step-Promotion")).toBeTruthy();
  });

  it("shows blocking reason for blocked steps", () => {
    render(<StrategyJourney steps={mockSteps} strategyId="strat_001" />);
    const blockingEl = screen.getByTestId("blocking-reason");
    expect(blockingEl.textContent).toContain("BLOCK_EVIDENCE_MISSING");
  });

  it("shows truncated artifact hash", () => {
    render(<StrategyJourney steps={mockSteps} strategyId="strat_001" />);
    const hashEls = screen.getAllByTestId("artifact-hash");
    expect(hashEls.length).toBeGreaterThan(0);
    expect(hashEls[0].textContent).toContain("aaaaaaaaaaaa...");
  });

  it("does not render live execution CTA", () => {
    const { container } = render(<StrategyJourney steps={mockSteps} strategyId="strat_001" />);
    expect(container.textContent).not.toContain("Start live trading");
    expect(container.textContent).not.toContain("Execute order");
  });
});
