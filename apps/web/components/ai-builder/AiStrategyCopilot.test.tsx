import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { AiStrategyCopilot } from "./AiStrategyCopilot";

const generatedSpec = {
  version: "0.1.0-draft.1",
  stage: "draft",
  status: "draft",
  validation: { output_mode: "signal_preview_only" },
};

function fetchCalls(fetchMock: ReturnType<typeof vi.fn>) {
  return fetchMock.mock.calls.map(([input, init]) => ({
    url: String(input),
    body: init?.body ? JSON.parse(String(init.body)) : undefined,
  }));
}

function adapterResponse() {
  return Response.json([{ adapter_id: "binance_perp", venue: "BINANCE" }]);
}

function promptTextArea() {
  return screen.getByRole("textbox");
}

async function waitForAdapterLoad() {
  await waitFor(() => expect(screen.getByText("binance_perp — BINANCE")).toBeInTheDocument());
}

beforeEach(() => {
  vi.spyOn(Date, "now").mockReturnValue(1_803_264_000_000);
});

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

describe("AiStrategyCopilot", () => {
  it("generates, applies, and saves the same accepted StrategySpec", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(adapterResponse())
      .mockResolvedValueOnce(
        Response.json({
          accepted: true,
          explanation: "Draft generated in advisory mode.",
          validation_errors: [],
          spec: generatedSpec,
        }),
      )
      .mockResolvedValueOnce(
        Response.json({
          ai_thread_id: "thread_1803264000000",
          improvement_cycle_id: "cycle_1803264000000",
          strategy_lineage_id: "lineage_1803264000000",
          strategy_version_id: "v_1803264000000",
          stage: "draft",
          mode: "advisory_only",
          spec: generatedSpec,
        }),
      )
      .mockResolvedValueOnce(
        Response.json({
          strategy_id: "strategy_001",
          strategy_version_id: "strategy_001_v001",
          spec: generatedSpec,
          adapter_id: "binance_perp",
          status: "draft",
        }),
      );
    vi.stubGlobal("fetch", fetchMock);

    render(<AiStrategyCopilot />);
    await waitForAdapterLoad();

    fireEvent.change(promptTextArea(), {
      target: { value: "Build an EMA RSI pullback strategy for BTC perpetuals" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Generate & Build Strategy" }));

    expect(await screen.findByText("Strategy built & saved")).toBeInTheDocument();
    expect(screen.getByText("Strategy strategy_001 saved as draft — pending backtest.")).toBeInTheDocument();

    const calls = fetchCalls(fetchMock);
    expect(calls[1]).toMatchObject({
      url: "/api/ai-builder/draft",
      body: {
        prompt: "Build an EMA RSI pullback strategy for BTC perpetuals",
        ai_thread_id: "thread_1803264000000",
        improvement_cycle_id: "cycle_1803264000000",
      },
    });
    expect(calls[2]).toMatchObject({
      url: "/api/ai-builder/apply",
      body: {
        prompt: "Build an EMA RSI pullback strategy for BTC perpetuals",
        strategy_lineage_id: "lineage_1803264000000",
        strategy_version_id: "v_1803264000000",
        spec: generatedSpec,
      },
    });
    expect(calls[3]).toMatchObject({
      url: "/api/strategies",
      body: {
        spec: generatedSpec,
        adapter_id: "binance_perp",
        status: "draft",
      },
    });
  });

  it("surfaces save failures and does not present the draft as saved", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(adapterResponse())
      .mockResolvedValueOnce(
        Response.json({
          accepted: true,
          explanation: "Draft generated in advisory mode.",
          validation_errors: [],
          spec: generatedSpec,
        }),
      )
      .mockResolvedValueOnce(
        Response.json({
          ai_thread_id: "thread_1803264000000",
          improvement_cycle_id: "cycle_1803264000000",
          strategy_lineage_id: "lineage_1803264000000",
          strategy_version_id: "v_1803264000000",
          stage: "draft",
          mode: "advisory_only",
          spec: generatedSpec,
        }),
      )
      .mockResolvedValueOnce(
        Response.json({ body: "Strategy registry write failed" }, { status: 500 }),
      );
    vi.stubGlobal("fetch", fetchMock);

    render(<AiStrategyCopilot />);
    await waitForAdapterLoad();

    fireEvent.change(promptTextArea(), {
      target: { value: "Build an EMA RSI pullback strategy for BTC perpetuals" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Generate & Build Strategy" }));

    expect(await screen.findByText("Failed")).toBeInTheDocument();
    expect(screen.getByText(/Nautilus Builder API request failed \(500\) for \/api\/strategies/)).toBeInTheDocument();
    await waitFor(() => expect(screen.queryByText("Strategy built & saved")).toBeNull());
  });

  it("does not save rejected drafts", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(adapterResponse())
      .mockResolvedValueOnce(
        Response.json({
          accepted: false,
          explanation: "Draft rejected until Builder schema and hard-rule validation pass.",
          validation_errors: ["forbidden credential request"],
          spec: {},
        }),
      );
    vi.stubGlobal("fetch", fetchMock);

    render(<AiStrategyCopilot />);
    await waitForAdapterLoad();

    fireEvent.change(promptTextArea(), {
      target: { value: "Use an API key in the strategy" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Generate & Build Strategy" }));

    expect(await screen.findByText("Failed")).toBeInTheDocument();
    expect(screen.getAllByText("forbidden credential request").length).toBeGreaterThan(0);
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
  });
});
