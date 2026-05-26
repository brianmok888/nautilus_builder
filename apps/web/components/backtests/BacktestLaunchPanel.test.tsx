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


  it("runs the created job through the backend BacktestNode trigger and displays events/artifacts", async () => {
    const artifactRef = "artifact://builder/project_alpha/user_123/backtests/bt_backtest_001/strategy_spec_replay.json";
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url === "/api/backtest-jobs") {
        return Response.json(
          {
            job_id: "bt_backtest_001",
            status: "queued",
            stage: "CREATED",
            lifecycle_status: "CREATED",
            strategy_spec_version_id: "sv_validated_001",
            adapter_profile_id: "BINANCE_PERP",
            instrument_id: "BTCUSDT-PERP",
            dataset_id: "ds_binance_btcusdt_1m",
            worker_id: "unassigned",
            result_artifact_refs: {},
            event_stream_id: "builder:runtime:bt_backtest_001",
            cancel_requested: false,
            compile_hash: "a".repeat(64),
            mode: "backend_owned",
          },
          { status: 201 },
        );
      }
      expect(url).toBe("/api/backtest-jobs/bt_backtest_001/run");
      expect(init?.method).toBe("POST");
      expect(String(init?.body)).toBe("{}");
      return Response.json({
        mode: "backend_owned_backtestnode",
        job: {
          job_id: "bt_backtest_001",
          status: "succeeded",
          stage: "SUCCEEDED",
          lifecycle_status: "SUCCEEDED",
          strategy_spec_version_id: "sv_validated_001",
          adapter_profile_id: "BINANCE_PERP",
          instrument_id: "BTCUSDT-PERP",
          dataset_id: "ds_binance_btcusdt_1m",
          worker_id: "nautilus-builder-worker:test",
          result_artifact_refs: { strategy_spec_replay: artifactRef },
          event_stream_id: "builder:runtime:bt_backtest_001",
          cancel_requested: false,
          compile_hash: "a".repeat(64),
          mode: "backend_owned",
        },
        result: {
          engine_mode: "strategy_spec_catalog_replay",
          dataset_source: "user_catalog",
          catalog_backed: true,
          orders: 0,
          positions: 0,
          execution_authority: false,
          credentials_used: false,
        },
        events: [
          {
            event_id: "bt_backtest_001_evt_000001",
            job_id: "bt_backtest_001",
            actor_type: "worker",
            actor_id: "nautilus-builder-worker:test",
            stage: "RUNNING",
            level: "INFO",
            message: "Backtest worker started",
            timestamp: "2026-05-26T00:00:00Z",
            metadata: {},
            progress_pct: 5,
          },
          {
            event_id: "bt_backtest_001_evt_000002",
            job_id: "bt_backtest_001",
            actor_type: "worker",
            actor_id: "nautilus-builder-worker:test",
            stage: "SUCCEEDED",
            level: "INFO",
            message: "Backtest worker succeeded",
            timestamp: "2026-05-26T00:00:01Z",
            metadata: { artifact_refs: { strategy_spec_replay: artifactRef } },
            progress_pct: 100,
          },
        ],
      });
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<BacktestLaunchPanel />);
    fireEvent.click(screen.getByRole("button", { name: "Create backtest job" }));

    await waitFor(() => expect(screen.getByText("Job queued: bt_backtest_001")).toBeInTheDocument());
    fireEvent.click(screen.getByRole("button", { name: "Run BacktestNode" }));

    await waitFor(() => expect(screen.getByText("BacktestNode run succeeded")).toBeInTheDocument());
    expect(screen.getAllByText("backend_owned_backtestnode").length).toBeGreaterThan(0);
    expect(screen.getByText("strategy_spec_catalog_replay")).toBeInTheDocument();
    expect(screen.getByText("artifact://builder/project_alpha/user_123/backtests/bt_backtest_001/strategy_spec_replay.json")).toBeInTheDocument();
    expect(screen.getByText("RUNNING")).toBeInTheDocument();
    expect(screen.getByText("SUCCEEDED")).toBeInTheDocument();
    expect(screen.getByText("orders: 0")).toBeInTheDocument();
    expect(screen.getByText("positions: 0")).toBeInTheDocument();
    expect(screen.getByText("execution_authority: false")).toBeInTheDocument();
    expect(screen.getByText("credentials_used: false")).toBeInTheDocument();
    await waitFor(() => expect(screen.getByRole("button", { name: /Run BacktestNode/ })).toBeDisabled());
    expect(screen.queryByText(/api key/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/submit order/i)).not.toBeInTheDocument();
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
