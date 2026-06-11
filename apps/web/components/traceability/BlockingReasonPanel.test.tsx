import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import BlockingReasonPanel from "./BlockingReasonPanel";

describe("BlockingReasonPanel", () => {
  it("renders blocking reasons", () => {
    render(
      <BlockingReasonPanel
        reasons={[
          { code: "BLOCK_EVIDENCE_MISSING", message: "Backtest result required", evidenceRequired: "backtest_result" },
        ]}
      />
    );
    expect(screen.getByTestId("blocking-reason-panel")).toBeTruthy();
    expect(screen.getByTestId("blocking-reason-BLOCK_EVIDENCE_MISSING")).toBeTruthy();
  });

  it("shows required evidence", () => {
    render(
      <BlockingReasonPanel
        reasons={[
          { code: "BLOCK_SYNTHETIC_ONLY", message: "Real replay required", evidenceRequired: "real_dataset_replay" },
        ]}
      />
    );
    expect(screen.getByText("Required: real_dataset_replay")).toBeTruthy();
  });

  it("returns null when no reasons", () => {
    const { container } = render(<BlockingReasonPanel reasons={[]} />);
    expect(container.innerHTML).toBe("");
  });
});
