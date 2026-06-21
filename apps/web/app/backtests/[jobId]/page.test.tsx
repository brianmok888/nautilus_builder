import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import BacktestJobPage from "./page";

const fetchBacktestJob = vi.fn();
const fetchBacktestJobEvents = vi.fn();
const cancelBacktestJob = vi.fn();

vi.mock("../../../../lib/api", () => ({
  fetchBacktestJob: (...args: unknown[]) => fetchBacktestJob(...args),
  fetchBacktestJobEvents: (...args: unknown[]) => fetchBacktestJobEvents(...args),
  cancelBacktestJob: (...args: unknown[]) => cancelBacktestJob(...args),
}));

describe("BacktestJobPage", () => {
  it("loads and renders backend job status, events, artifacts, and cancel state", async () => {
    fetchBacktestJob.mockResolvedValue({
      job_id: "bt_123",
      status: "running",
      stage: "RUNNING",
      lifecycle_status: "RUNNING",
      created_by: "builder_api",
      created_at: "2026-05-26T00:00:00Z",
      updated_at: "2026-05-26T00:01:00Z",
      strategy_spec_version_id: "strategy_001_v001",
      adapter_profile_id: "BINANCE_PERP",
      instrument_id: "BTCUSDT-PERP",
      data_range: "2025-01-01/2025-06-01",
      data_type: "bars",
      timeframe: "5-MINUTE",
      market_type: "perp",
      worker_id: "worker-7",
      result_artifact_refs: {
        result_json: "artifacts/bt_123/result.json",
        report: "artifacts/bt_123/report.html",
      },
      event_stream_id: "builder:runtime:bt_123",
      cancel_requested: false,
      compile_hash: "a".repeat(64),
      mode: "backend_owned",
    });
    fetchBacktestJobEvents.mockResolvedValue({
      job_id: "bt_123",
      stream_name: "builder:runtime:bt_123",
      mode: "observational",
      events: [
        {
          event_id: "bt_123_evt_000001",
          stage: "RUNNING",
          level: "INFO",
          message: "Worker started replay",
          actor_id: "worker-7",
          timestamp: "2026-05-26T00:01:00Z",
          metadata: { progress_pct: 50 },
        },
      ],
    });
    cancelBacktestJob.mockResolvedValue({
      job_id: "bt_123",
      status: "cancel_requested",
      stage: "CANCEL_REQUESTED",
      cancel_requested: true,
    });

    render(await BacktestJobPage({ params: Promise.resolve({ jobId: "bt_123" }) }));

    expect(fetchBacktestJob).toHaveBeenCalledWith("bt_123");
    expect(fetchBacktestJobEvents).toHaveBeenCalledWith("bt_123");
    expect(screen.getAllByText("running").length).toBeGreaterThan(0);
    expect(screen.getAllByText("worker-7").length).toBeGreaterThan(0);
    expect(screen.getAllByText("strategy_001_v001").length).toBeGreaterThan(0);
    expect(screen.getByText("result_json")).toBeInTheDocument();
    expect(screen.getByText("artifacts/bt_123/result.json")).toBeInTheDocument();
    expect(screen.getByText("Worker started replay")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /request cancel/i }));

    await waitFor(() => expect(cancelBacktestJob).toHaveBeenCalledWith("bt_123"));
    expect((await screen.findAllByText("cancel_requested")).length).toBeGreaterThan(0);
  });
});
