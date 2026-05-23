import { render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { StrategyDetailClient } from "./StrategyDetailClient";

afterEach(() => vi.restoreAllMocks());

it("renders backend version history for a stable strategy id", async () => {
  vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
    new Response(JSON.stringify({ strategy_id: "strategy_001", strategy_lineage_id: "lineage_strategy_001", versions: [{ strategy_version_id: "strategy_001_v001", spec: { version: "0.1.0-draft.1" } }] }), { status: 200 }),
  );

  render(<StrategyDetailClient strategyId="strategy_001" />);

  expect(await screen.findByText("lineage_strategy_001")).toBeInTheDocument();
  expect(screen.getByText("strategy_001_v001")).toBeInTheDocument();
});
