import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { Modal } from "antd";
import { afterEach, describe, expect, test, vi } from "vitest";

import { PipelineRunPanel } from "./PipelineRunPanel";

const validSpec = {
  strategy_name: "ema_rsi_pullback",
  entry_signal: { type: "cross", fast_period: 10, slow_period: 20 },
  exit_signal: { type: "opposite_signal" },
};

function pipelineResponse(promotionEvidence: Record<string, string>) {
  return {
    success: true,
    steps: [
      { step: "validate", status: "completed" },
      { step: "compile", status: "completed" },
      { step: "backtest", status: "completed" },
      { step: "results", status: "completed" },
    ],
    validation_report: { status: "passed" },
    compile_artifact: {
      compile_hash: "compile_hash_001",
      strategy_version: "strategy_v001",
    },
    backtest_result: {
      trade_count: 3,
      total_pnl: 12.5,
      win_rate: 0.67,
    },
    promotion_evidence: promotionEvidence,
    promotion_status: "pending_approval",
  };
}

function renderWithPipelineResponse(response: unknown) {
  const fetchMock = vi.fn().mockImplementation((input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    if (url === "/api/pipeline/run") {
      return Promise.resolve(Response.json(response));
    }
    if (url === "/api/pipeline/promote") {
      return Promise.resolve(Response.json({
        success: true,
        promotion_status: "manual_approval_pending",
        promotion_request: {},
        error: null,
      }));
    }
    return Promise.reject(new Error(`unexpected fetch: ${url}`));
  });
  vi.stubGlobal("fetch", fetchMock);

  render(<PipelineRunPanel />);
  fireEvent.change(screen.getByRole("textbox"), {
    target: { value: JSON.stringify(validSpec, null, 2) },
  });
  const runButton = screen.getByText("Run Pipeline").closest("button");
  expect(runButton).not.toBeNull();
  fireEvent.click(runButton!);
  return fetchMock;
}

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

describe("PipelineRunPanel", () => {
  test("disables shadow promotion and shows missing evidence refs", async () => {
    renderWithPipelineResponse(pipelineResponse({
      validation_report: "artifact://validation/report.json",
    }));

    expect(await screen.findByText("Promotion Evidence")).toBeTruthy();
    expect(screen.getByText("Missing Evidence")).toBeTruthy();
    expect(screen.getByText("backtest_result")).toBeTruthy();
    expect(screen.getByText("gate_compatibility_report")).toBeTruthy();
    expect(screen.getByText("Request Shadow Promotion").closest("button")).toBeDisabled();
  });

  test("submits complete backend evidence refs for shadow promotion", async () => {
    const confirmSpy = vi.spyOn(Modal, "confirm").mockImplementation((config) => {
      void config.onOk?.(() => undefined);
      return { destroy: vi.fn(), update: vi.fn() };
    });
    const fetchMock = renderWithPipelineResponse(pipelineResponse({
      validation_report: "artifact://validation/report.json",
      backtest_result: "artifact://backtests/result.json",
      gate_compatibility_report: "artifact://gate/report.json",
    }));

    expect(await screen.findByText("Promotion Evidence")).toBeTruthy();
    const promoteButton = screen.getByText("Request Shadow Promotion").closest("button");
    expect(promoteButton).not.toBeNull();
    fireEvent.click(promoteButton!);

    expect(confirmSpy).toHaveBeenCalled();
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
    const promoteCall = fetchMock.mock.calls.find(([input]) => String(input) === "/api/pipeline/promote");
    expect(promoteCall).toBeDefined();
    const body = JSON.parse(String(promoteCall?.[1]?.body));
    expect(body.evidence_refs).toEqual({
      validation_report: "artifact://validation/report.json",
      backtest_result: "artifact://backtests/result.json",
      gate_compatibility_report: "artifact://gate/report.json",
    });
  });
});
