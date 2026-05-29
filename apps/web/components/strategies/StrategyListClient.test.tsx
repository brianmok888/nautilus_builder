import { render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { StrategyListClient } from "./StrategyListClient";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

afterEach(() => vi.restoreAllMocks());

describe("StrategyListClient", () => {
  it("loads and renders strategies with status chips", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
      new Response(
        JSON.stringify([
          {
            strategy_id: "strategy_001",
            strategy_lineage_id: "lineage_strategy_001",
            status: "draft",
            latest_spec: { version: "0.1.0-draft.1" },
          },
          {
            strategy_id: "strategy_002",
            strategy_lineage_id: "lineage_strategy_002",
            status: "approved",
            latest_spec: { version: "1.0.0" },
          },
        ]),
        { status: 200 },
      ),
    );

    render(<StrategyListClient />);

    // Table shows loading spinner, not text; just wait for data
    await waitFor(() => expect(screen.getByText("strategy_001")).toBeInTheDocument());
    expect(screen.getByText("lineage_strategy_001")).toBeInTheDocument();
    expect(screen.getByText("strategy_002")).toBeInTheDocument();
    expect(screen.getByText("draft")).toBeInTheDocument();
    expect(screen.getByText("approved")).toBeInTheDocument();
  });

  it("shows empty state when no strategies exist", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
      new Response(JSON.stringify([]), { status: 200 }),
    );

    render(<StrategyListClient />);

    await waitFor(() =>
      expect(screen.getByText(/No strategies yet/)).toBeInTheDocument(),
    );
  });

  it("renders Edit, Clone, Backtest action buttons per row", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
      new Response(
        JSON.stringify([
          {
            strategy_id: "strategy_001",
            strategy_lineage_id: "lineage_001",
            status: "validated",
            latest_spec: {},
          },
        ]),
        { status: 200 },
      ),
    );

    render(<StrategyListClient />);
    await waitFor(() => expect(screen.getByText("strategy_001")).toBeInTheDocument());

    // All three action buttons should be present
    expect(screen.getAllByText("Edit").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Clone").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Backtest").length).toBeGreaterThan(0);
  });

  it("disables Edit for approved strategies", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
      new Response(
        JSON.stringify([
          {
            strategy_id: "strategy_approved",
            strategy_lineage_id: "lineage_approved",
            status: "approved",
            latest_spec: {},
          },
        ]),
        { status: 200 },
      ),
    );

    render(<StrategyListClient />);
    await waitFor(() => expect(screen.getByText("strategy_approved")).toBeInTheDocument());

    // Edit button should be disabled for approved
    const editButtons = screen.getAllByText("Edit");
    const editBtn = editButtons[0].closest("button")!;
    expect(editBtn.disabled).toBe(true);
  });
});
