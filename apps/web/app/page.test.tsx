import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import HomePage from "./page";

vi.mock("next/navigation", () => ({
  useSearchParams: () => new URLSearchParams(),
}));

vi.mock("../components/dashboard/BuilderDashboard", () => ({
  BuilderDashboard: ({ initialTab }: { readonly initialTab?: string }) => (
    <div data-testid="dashboard-initial-tab">{initialTab}</div>
  ),
}));

describe("HomePage", () => {
  it("renders Overview at bare root when no tab query is present", () => {
    render(<HomePage />);

    expect(screen.getByTestId("dashboard-initial-tab")).toHaveTextContent("overview");
  });
});
