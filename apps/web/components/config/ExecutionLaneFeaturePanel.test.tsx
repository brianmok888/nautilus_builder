import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ExecutionLaneFeaturePanel } from "./ExecutionLaneFeaturePanel";

function statusPayload(overrides = {}) {
  return {
    mode: "execution_lane",
    runtime_profile_id: null,
    profiles: 0,
    queued_commands: 0,
    claimed_commands: 0,
    reported_commands: 0,
    reports: 0,
    venue_bindings: [],
    ui_features: {
      execution_lane_ui_enabled: false,
      paper_controls_enabled: false,
      live_controls_enabled: false,
      credential_inputs_allowed: false,
      strategy_lane_coupled: false,
    },
    strategy_lane_coupled: false,
    may_submit_order: false,
    ...overrides,
  };
}

describe("ExecutionLaneFeaturePanel", () => {
  afterEach(() => vi.restoreAllMocks());

  it("fully wires paper TradingNode profile, runtime plan, command enqueue, and backend worker report", async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      const method = init?.method ?? "GET";
      if (url.startsWith("/api/execution-lane/status")) {
        return Response.json(statusPayload());
      }
      if (url === "/api/execution-lane/profiles" && method === "POST") {
        const payload = JSON.parse(String(init?.body));
        expect(payload).toMatchObject({
          runtime_profile_id: "rp_paper_tradingnode",
          lane_mode: "paper",
          paper_trading_enabled: true,
          adapter_id: "BINANCE_PERP",
          venue: "BINANCE",
          ui_enabled: true,
          paper_controls_enabled: true,
        });
        expect(JSON.stringify(payload).toLowerCase()).not.toContain("api_key");
        return Response.json({ ...payload, strategy_lane_coupled: false }, { status: 201 });
      }
      if (url.startsWith("/api/execution-lane/runtime-plan") && method === "GET") {
        return Response.json({
          schema_version: "execution_lane.tradingnode.v1",
          tenant_id: "tenant_a",
          project_id: "project_alpha",
          runtime_profile_id: "rp_paper_tradingnode",
          lane_mode: "paper",
          readiness_status: "READY",
          blocked_reasons: [],
          node_runtime: "python_trading_node",
          runtime_label: "python_live_integration_specific",
          future_runtime: "rust_live_node",
          runtime_environment: "sandbox",
          adapter_id: "BINANCE_PERP",
          venue: "BINANCE",
          venue_account_id: "SIM-BINANCE-001",
          strategy_lane_coupled: false,
          browser_credentials_allowed: false,
          credential_inputs_allowed: false,
          live_trading_enabled: false,
          execution_authority: false,
          may_submit_order: false,
          advisory_only: true,
          manual_review_required: true,
          reconciliation_required: true,
          credential_slot_ref: null,
          risk_profile_id: null,
          strategy_lineage_id: null,
          strategy_version_id: null,
          trade_action_id: null,
          promotion_approval_id: null,
          manual_review_id: null,
          config_checksum: null,
          evidence_refs: {},
          nautilus_imports: ["nautilus_trader.live.node.TradingNode"],
          config_contract: { exec_engine: { reconciliation: true, reconciliation_lookback_mins: 60 } },
          nautilus_trader_version: "1.223.0",
        });
      }
      if (url === "/api/execution-lane/commands" && method === "POST") {
        const payload = JSON.parse(String(init?.body));
        expect(payload).toMatchObject({
          runtime_profile_id: "rp_paper_tradingnode",
          lane_mode: "paper",
          adapter_id: "BINANCE_PERP",
          venue: "BINANCE",
          strategy_lineage_id: "lineage_ema_rsi",
          strategy_version_id: "strategy_001_v004",
          order_intent: { side: "BUY", instrument_id: "BTCUSDT-PERP.BINANCE", quantity: "0.01" },
        });
        expect(payload.may_submit_order).toBeUndefined();
        return Response.json({ ...payload, command_id: "exec_cmd_paper_001", status: "QUEUED", may_submit_order: false }, { status: 201 });
      }
      if (url === "/api/execution-lane/worker/run-once" && method === "POST") {
        const payload = JSON.parse(String(init?.body));
        expect(payload).toEqual({ runtime_profile_id: "rp_paper_tradingnode", worker_id: "web_execution_worker" });
        return Response.json(
          {
            report_id: "exec_report_001",
            command_id: "exec_cmd_paper_001",
            runtime_profile_id: "rp_paper_tradingnode",
            tenant_id: "tenant_a",
            project_id: "project_alpha",
            lane_mode: "paper",
            adapter_id: "BINANCE_PERP",
            venue_account_id: "SIM-BINANCE-001",
            report_type: "tradingnode_runtime_plan",
            venue: "BINANCE",
            instrument_id: "BTCUSDT-PERP.BINANCE",
            strategy_lane_coupled: false,
            payload: {
              node_runtime: "python_trading_node",
              runtime_label: "python_live_integration_specific",
              may_submit_order: false,
              browser_credentials_allowed: false,
            },
          },
          { status: 202 },
        );
      }
      throw new Error(`unexpected fetch ${method} ${url}`);
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<ExecutionLaneFeaturePanel />);

    expect(await screen.findByText("Feature visibility matrix")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Wire paper profile" }));
    await waitFor(() => expect(screen.getByText("Runtime plan READY")).toBeInTheDocument());

    fireEvent.click(screen.getByRole("button", { name: "Queue paper command" }));
    await waitFor(() => expect(screen.getByText("Command queued: exec_cmd_paper_001")).toBeInTheDocument());

    fireEvent.click(screen.getByRole("button", { name: "Run backend worker plan" }));
    await waitFor(() => expect(screen.getByText("Worker report: tradingnode_runtime_plan")).toBeInTheDocument());

    expect(screen.getByText("python_live_integration_specific")).toBeInTheDocument();
    expect(screen.queryByLabelText(/api key/i)).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /submit order/i })).not.toBeInTheDocument();
  });
});
