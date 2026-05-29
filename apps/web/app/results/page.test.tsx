import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import ResultsPage from "./page";

vi.mock("../../components/results/ResultsListClient", () => ({
  ResultsListClient: () => <div data-testid="results-list">Results List</div>,
}));

// Mock next navigation
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

describe("ResultsPage", () => {
  it("renders the results list client component", () => {
    render(<ResultsPage />);
    expect(screen.getByTestId("results-list")).toBeTruthy();
  });
});
