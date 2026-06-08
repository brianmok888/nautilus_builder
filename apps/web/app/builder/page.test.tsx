import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import BuilderPage from "./page";

vi.mock("../../components/dashboard/BuilderDashboard", () => ({
  BuilderDashboard: ({ initialTab }: { readonly initialTab?: string }) => (
    <div data-testid="dashboard-initial-tab">{initialTab}</div>
  ),
}));

describe("BuilderPage", () => {
  it("renders the Strategy Builder dashboard lane at /builder", () => {
    render(<BuilderPage />);

    expect(screen.getByTestId("dashboard-initial-tab")).toHaveTextContent("strategy");
  });
});
