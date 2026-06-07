import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { BuilderSafetyBanner } from "./BuilderSafetyBanner";

describe("BuilderSafetyBanner", () => {
  it("says Builder does not submit live orders", () => {
    render(<BuilderSafetyBanner />);
    expect(screen.getByText("Builder-only mode")).toBeTruthy();
    expect(
      screen.getByText(/does not submit live orders/i),
    ).toBeTruthy();
  });

  it("mentions drafts, validation, replay evidence", () => {
    render(<BuilderSafetyBanner />);
    const text = screen.getByRole("alert").textContent ?? "";
    expect(text).toContain("strategy drafts");
    expect(text).toContain("replay evidence");
    expect(text).toContain("promotion requests");
  });
});
