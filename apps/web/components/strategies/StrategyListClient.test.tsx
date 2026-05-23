import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { StrategyListClient } from "./StrategyListClient";

afterEach(() => vi.restoreAllMocks());

describe("StrategyListClient", () => {
  it("loads and renders strategies from the backend", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
      new Response(JSON.stringify([{ strategy_id: "strategy_001", strategy_lineage_id: "lineage_strategy_001", latest_spec: { version: "0.1.0-draft.1" } }]), { status: 200 }),
    );

    render(<StrategyListClient />);

    expect(screen.getByText("Loading strategies…")).toBeInTheDocument();
    expect(await screen.findByText("strategy_001")).toBeInTheDocument();
    expect(screen.getByText("lineage_strategy_001")).toBeInTheDocument();
  });

  it("submits a new draft and renders the result", async () => {
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(new Response(JSON.stringify([]), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ strategy_id: "strategy_001", strategy_lineage_id: "lineage_strategy_001", strategy_version_id: "strategy_001_v001", spec: { version: "0.1.0-draft.1" } }), { status: 201 }));

    render(<StrategyListClient />);
    await screen.findByText("No saved strategies yet.");
    fireEvent.click(screen.getByRole("button", { name: "Create draft" }));

    await waitFor(() => expect(screen.getByText("strategy_001")).toBeInTheDocument());
  });
});
