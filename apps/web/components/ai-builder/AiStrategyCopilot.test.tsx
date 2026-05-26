import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { AiStrategyCopilot } from "./AiStrategyCopilot";

function fetchCalls(fetchMock: ReturnType<typeof vi.fn>) {
  return fetchMock.mock.calls.map(([input, init]) => ({
    url: String(input),
    body: init?.body ? JSON.parse(String(init.body)) : undefined,
  }));
}

describe("AiStrategyCopilot", () => {
  it("turns an operator prompt into an accepted StrategySpec and applies it with lineage IDs", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        Response.json({
          accepted: true,
          explanation: "Draft generated in advisory mode.",
          validation_errors: [],
          spec: {
            version: "0.1.0-draft.1",
            stage: "draft",
            status: "draft",
            validation: { output_mode: "signal_preview_only" },
          },
        }),
      )
      .mockResolvedValueOnce(
        Response.json({
          ai_thread_id: "thread_ui_default",
          improvement_cycle_id: "cycle_ui_default",
          strategy_lineage_id: "lineage_strategy_001",
          strategy_version_id: "strategy_001_v001",
          stage: "draft",
          mode: "advisory_only",
          spec: { version: "0.1.0-draft.1", stage: "draft" },
        }),
      );
    vi.stubGlobal("fetch", fetchMock);

    render(<AiStrategyCopilot />);

    expect(screen.getByLabelText("Strategy prompt")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Apply to Builder" })).toBeDisabled();

    fireEvent.change(screen.getByLabelText("Strategy prompt"), {
      target: { value: "Build an EMA RSI pullback strategy for BTC perpetuals" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Generate StrategySpec" }));

    expect(await screen.findByText("Accepted draft")).toBeInTheDocument();
    expect(screen.getByText("Draft generated in advisory mode.")).toBeInTheDocument();
    expect(screen.getByText(/"output_mode": "signal_preview_only"/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Apply to Builder" })).toBeEnabled();

    fireEvent.click(screen.getByRole("button", { name: "Apply to Builder" }));

    expect(await screen.findByText("Applied to Builder draft")).toBeInTheDocument();
    const calls = fetchCalls(fetchMock);
    expect(calls[0]).toMatchObject({
      url: "/api/ai-builder/draft",
      body: {
        prompt: "Build an EMA RSI pullback strategy for BTC perpetuals",
        ai_thread_id: "thread_ui_default",
        improvement_cycle_id: "cycle_ui_default",
      },
    });
    expect(calls[1]).toMatchObject({
      url: "/api/ai-builder/apply",
      body: {
        prompt: "Build an EMA RSI pullback strategy for BTC perpetuals",
        ai_thread_id: "thread_ui_default",
        improvement_cycle_id: "cycle_ui_default",
        strategy_lineage_id: "lineage_strategy_001",
        strategy_version_id: "strategy_001_v001",
      },
    });
  });

  it("keeps Apply disabled for rejected drafts and shows validation errors", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValueOnce(
        Response.json({
          accepted: false,
          explanation: "Draft rejected until Builder schema and hard-rule validation pass.",
          validation_errors: ["forbidden credential request"],
          spec: {},
        }),
      ),
    );

    render(<AiStrategyCopilot />);

    fireEvent.change(screen.getByLabelText("Strategy prompt"), {
      target: { value: "Use an API key in the strategy" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Generate StrategySpec" }));

    expect(await screen.findByText("Rejected draft")).toBeInTheDocument();
    expect(screen.getByText("forbidden credential request")).toBeInTheDocument();
    await waitFor(() =>
      expect(screen.getByRole("button", { name: "Apply to Builder" })).toBeDisabled(),
    );
  });
});
