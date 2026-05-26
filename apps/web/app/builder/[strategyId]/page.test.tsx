import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import BuilderStrategyPage from "./page";

describe("BuilderStrategyPage", () => {
  it("provides a real strategy-scoped builder route for detail-page links", async () => {
    render(await BuilderStrategyPage({ params: Promise.resolve({ strategyId: "strategy_001" }) }));

    expect(screen.getByText("Builder workspace for strategy_001")).toBeInTheDocument();
    expect(screen.getByText("Describe strategy")).toBeInTheDocument();
    expect(screen.getByText(/draft-only builder route/i)).toBeInTheDocument();
  });
});
