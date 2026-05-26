import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { BacktestLaunchPanel } from "./BacktestLaunchPanel";

describe("BacktestLaunchPanel", () => {
  afterEach(() => vi.restoreAllMocks());

  it("creates a backend-owned backtest job from a complete validated run manifest", async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      expect(String(input)).toBe("/api/backtest-jobs");
      expect(init?.method).toBe("POST");
      const payload = JSON.parse(String(init?.body));
      expect(payload).toMatchObject({
        strategy_version_id: "sv_validated_001",
        adapter_profile_id: "BINANCE_PERP",
        instrument_id: "BTCUSDT-PERP",
        validation_report_id: "vr_validated_001",
        dataset_id: "ds_binance_btcusdt_1m",
        data_range: "2024-01-01:2024-03-01",
        data_type: "historical_bars",
        timeframe: "1m",
        market_type: "crypto_perp",
        created_by: "builder_web",
      });
      expect(payload.compile_hash).toMatch(/^[a-f0-9]{64}$/);
      return Response.json(
        {
          job_id: "bt_backtest_001",
          status: "queued",
          stage: "CREATED",
          lifecycle_status: "CREATED",
          strategy_spec_version_id: "sv_validated_001",
          adapter_profile_id: "BINANCE_PERP",
          instrument_id: "BTCUSDT-PERP",
          data_range: "2024-01-01:2024-03-01",
          data_type: "historical_bars",
          timeframe: "1m",
          market_type: "crypto_perp",
          dataset_id: "ds_binance_btcusdt_1m",
          worker_id: "unassigned",
          result_artifact_refs: {},
          event_stream_id: "builder:runtime:bt_backtest_001",
          cancel_requested: false,
          compile_hash: payload.compile_hash,
          mode: "backend_owned",
        },
        { status: 201 },
      );
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<BacktestLaunchPanel />);

    expect(screen.getByText("Validated run manifest")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Create backtest job" })).toBeEnabled();
    fireEvent.click(screen.getByRole("button", { name: "Create backtest job" }));

    await waitFor(() => expect(screen.getByText("Job queued: bt_backtest_001")).toBeInTheDocument());
    expect(screen.getByRole("link", { name: "Open job console" })).toHaveAttribute("href", "/backtests/bt_backtest_001");
    expect(screen.getByText("may_submit_order: false")).toBeInTheDocument();
    expect(screen.queryByText(/submit order/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/deploy live/i)).not.toBeInTheDocument();
  });

  it("blocks job creation when compile evidence is not a sha256 hash", () => {
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);

    render(<BacktestLaunchPanel />);
    fireEvent.change(screen.getByLabelText("Compile hash"), { target: { value: "not-a-hash" } });

    expect(screen.getByRole("button", { name: "Create backtest job" })).toBeDisabled();
    expect(screen.getByText("compile_hash must be a 64-character sha256 digest")).toBeInTheDocument();
    expect(fetchMock).not.toHaveBeenCalled();
  });
});
