import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import ExecutionPage from "./page";

vi.mock("../../components/dashboard/BuilderDashboard", () => ({
  BuilderDashboard: ({ initialTab }: { readonly initialTab?: string }) => (
    <div data-testid="dashboard-initial-tab">{initialTab}</div>
  ),
}));

describe("ExecutionPage", () => {
  it("renders the Execution Lane dashboard lane at /execution", () => {
    render(<ExecutionPage />);

    expect(screen.getByTestId("dashboard-initial-tab")).toHaveTextContent("execution");
  });
});
