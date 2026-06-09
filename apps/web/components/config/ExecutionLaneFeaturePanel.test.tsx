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
    sessions: 0,
    running_sessions: 0,
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

  it("does not render browser credential bootstrap inputs", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL) => {
        if (String(input).startsWith("/api/execution-lane/status")) {
          return Response.json(statusPayload());
        }
        throw new Error(`unexpected fetch ${String(input)}`);
      }),
    );

    render(<ExecutionLaneFeaturePanel />);

    expect(await screen.findByText("Feature visibility matrix")).toBeInTheDocument();
    expect(screen.queryByLabelText("Credential variable 1")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Credential value 1")).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Save credential slot" })).not.toBeInTheDocument();
  });

  it("requests only backend-owned profile and runtime-plan visibility from the browser", async () => {
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
        expect(JSON.stringify(payload)).not.toContain("order_intent");
        expect(JSON.stringify(payload)).not.toContain("risk_decision");
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
      throw new Error(`unexpected browser runtime action ${method} ${url}`);
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<ExecutionLaneFeaturePanel />);

    expect(await screen.findByText("Feature visibility matrix")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Queue paper command" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Run backend worker plan" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Start Paper Session" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Stop / Dispose" })).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Wire paper profile" }));
    await waitFor(() => expect(screen.getByText("Runtime plan READY")).toBeInTheDocument());

    const requestedUrls = fetchMock.mock.calls.map(([input]) => String(input));
    expect(requestedUrls.some((url) => url === "/api/execution-lane/commands")).toBe(false);
    expect(requestedUrls.some((url) => url === "/api/execution-lane/worker/run-once")).toBe(false);
    expect(requestedUrls.some((url) => url === "/api/execution-lane/sessions/start")).toBe(false);
    expect(requestedUrls.some((url) => url.includes("/api/execution-lane/sessions/") && url.endsWith("/stop"))).toBe(false);
    expect(screen.getByText("python_live_integration_specific")).toBeInTheDocument();
    expect(screen.queryByLabelText(/api key/i)).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /submit order/i })).not.toBeInTheDocument();
  });

  it.skip("saves a local credential slot, clears secret fields, and binds only the slot ref to profiles", async () => {
    let savedSecretSeen = false;
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      const method = init?.method ?? "GET";
      if (url.startsWith("/api/execution-lane/status")) {
        return Response.json(statusPayload());
      }
      if (url === "/api/execution-lane/credential-slots" && method === "POST") {
        const payload = JSON.parse(String(init?.body));
        expect(payload).toMatchObject({
          runtime_profile_id: "rp_paper_tradingnode",
          venue: "BINANCE",
          lane_mode: "paper",
          credential_values: {
            BINANCE_API_KEY: "test-binance-key",
            BINANCE_API_SECRET: "test-binance-secret",
          },
        });
        savedSecretSeen = true;
        return Response.json(
          {
            credential_slot_ref: "credslot://local-env/project_alpha/rp_paper_tradingnode/binance",
            tenant_id: "tenant_a",
            project_id: "project_alpha",
            runtime_profile_id: "rp_paper_tradingnode",
            adapter_id: "BINANCE_PERP",
            venue: "BINANCE",
            lane_mode: "paper",
            secrets_storage: "local_env_file",
            env_file_path: ".env.execution.local",
            redacted_keys: ["BINANCE_API_KEY", "BINANCE_API_SECRET"],
            fingerprint: "a".repeat(64),
            browser_secret_echo: false,
          },
          { status: 201 },
        );
      }
      if (url === "/api/execution-lane/profiles" && method === "POST") {
        const payload = JSON.parse(String(init?.body));
        expect(payload.credential_slot_ref).toBe("credslot://local-env/project_alpha/rp_paper_tradingnode/binance");
        expect(JSON.stringify(payload)).not.toContain("test-binance-key");
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
          credential_slot_ref: "credslot://local-env/project_alpha/rp_paper_tradingnode/binance",
          evidence_refs: {},
          config_contract: { exec_engine: { reconciliation: true } },
        });
      }
      throw new Error(`unexpected fetch ${method} ${url}`);
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<ExecutionLaneFeaturePanel />);

    expect(await screen.findByText("Feature visibility matrix")).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Credential variable 1"), { target: { value: "BINANCE_API_KEY" } });
    fireEvent.change(screen.getByLabelText("Credential value 1"), { target: { value: "test-binance-key" } });
    fireEvent.change(screen.getByLabelText("Credential variable 2"), { target: { value: "BINANCE_API_SECRET" } });
    fireEvent.change(screen.getByLabelText("Credential value 2"), { target: { value: "test-binance-secret" } });
    fireEvent.click(screen.getByRole("button", { name: "Save credential slot" }));

    await waitFor(() => expect(screen.getByText("Credential slot ready")).toBeInTheDocument());
    expect(savedSecretSeen).toBe(true);
    expect(screen.getByText("credslot://local-env/project_alpha/rp_paper_tradingnode/binance")).toBeInTheDocument();
    expect(screen.queryByDisplayValue("test-binance-key")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Wire paper profile" }));
    await waitFor(() => expect(screen.getByText("Runtime plan READY")).toBeInTheDocument());
    expect(screen.queryByText("test-binance-secret")).not.toBeInTheDocument();
  });


  it.skip("starts and stops a paper TradingNode session from the web UI without exposing secrets", async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      const method = init?.method ?? "GET";
      if (url.startsWith("/api/execution-lane/status")) {
        return Response.json(statusPayload());
      }
      if (url === "/api/execution-lane/credential-slots" && method === "POST") {
        return Response.json({
          credential_slot_ref: "credslot://local-env/project_alpha/rp_paper_tradingnode/binance",
          tenant_id: "tenant_a",
          project_id: "project_alpha",
          runtime_profile_id: "rp_paper_tradingnode",
          adapter_id: "BINANCE_PERP",
          venue: "BINANCE",
          lane_mode: "paper",
          requested_by: "ops_user",
          secrets_storage: "local_env_file",
          env_file_path: ".env.execution.local",
          redacted_keys: ["BINANCE_API_KEY", "BINANCE_API_SECRET"],
          fingerprint: "a".repeat(64),
          browser_secret_echo: false,
        }, { status: 201 });
      }
      if (url === "/api/execution-lane/profiles" && method === "POST") {
        const payload = JSON.parse(String(init?.body));
        expect(payload.credential_slot_ref).toBe("credslot://local-env/project_alpha/rp_paper_tradingnode/binance");
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
          credential_slot_ref: "credslot://local-env/project_alpha/rp_paper_tradingnode/binance",
          evidence_refs: {},
          config_contract: { exec_engine: { reconciliation: true } },
        });
      }
      if (url === "/api/execution-lane/commands" && method === "POST") {
        const payload = JSON.parse(String(init?.body));
        return Response.json({ ...payload, command_id: "exec_cmd_paper_001", status: "QUEUED", may_submit_order: false }, { status: 201 });
      }
      if (url === "/api/execution-lane/sessions/start" && method === "POST") {
        const payload = JSON.parse(String(init?.body));
        expect(payload).toMatchObject({
          runtime_profile_id: "rp_paper_tradingnode",
          command_id: "exec_cmd_paper_001",
          worker_id: "web_execution_worker",
          project_id: "project_alpha",
        });
        return Response.json({
          session_id: "exec_session_001",
          command_id: "exec_cmd_paper_001",
          runtime_profile_id: "rp_paper_tradingnode",
          tenant_id: "tenant_a",
          project_id: "project_alpha",
          lane_mode: "paper",
          adapter_id: "BINANCE_PERP",
          venue: "BINANCE",
          venue_account_id: "SIM-BINANCE-001",
          status: "RUNNING",
          lifecycle_status: "RUNNING",
          runner_mode: "contract_dry_run",
          worker_id: "web_execution_worker",
          started_at: "2026-05-27T00:00:00Z",
          runtime_environment: "sandbox",
          node_runtime: "python_trading_node",
          runtime_label: "python_live_integration_specific",
          future_runtime: "rust_live_node",
          strategy_lineage_id: "lineage_ema_rsi",
          strategy_version_id: "strategy_001_v004",
          trade_action_id: "ta_paper_001",
          credential_slot_ref: "credslot://local-env/project_alpha/rp_paper_tradingnode/binance",
          credential_env_keys: ["BINANCE_API_KEY", "BINANCE_API_SECRET"],
          credential_values_resolved: true,
          tradingnode_config: { config_type: "TradingNodeConfig" },
          attached_strategy: { strategy_version_id: "strategy_001_v004", may_submit_order: false },
          lifecycle_events: [
            { status: "INITIALIZED", message: "accepted", timestamp: "2026-05-27T00:00:00Z", session_id: "exec_session_001" },
            { status: "RUNNING", message: "started", timestamp: "2026-05-27T00:00:01Z", session_id: "exec_session_001" },
          ],
          browser_credentials_allowed: false,
          credential_inputs_allowed: false,
          strategy_lane_coupled: false,
          live_trading_enabled: false,
          execution_authority: false,
          may_submit_order: false,
        }, { status: 202 });
      }
      if (url === "/api/execution-lane/sessions/exec_session_001/stop" && method === "POST") {
        return Response.json({
          session_id: "exec_session_001",
          command_id: "exec_cmd_paper_001",
          runtime_profile_id: "rp_paper_tradingnode",
          tenant_id: "tenant_a",
          project_id: "project_alpha",
          lane_mode: "paper",
          adapter_id: "BINANCE_PERP",
          venue: "BINANCE",
          venue_account_id: "SIM-BINANCE-001",
          status: "DISPOSED",
          lifecycle_status: "DISPOSED",
          runner_mode: "contract_dry_run",
          worker_id: "web_execution_worker",
          started_at: "2026-05-27T00:00:00Z",
          stopped_at: "2026-05-27T00:01:00Z",
          disposed_at: "2026-05-27T00:01:00Z",
          runtime_environment: "sandbox",
          node_runtime: "python_trading_node",
          runtime_label: "python_live_integration_specific",
          future_runtime: "rust_live_node",
          strategy_lineage_id: "lineage_ema_rsi",
          strategy_version_id: "strategy_001_v004",
          trade_action_id: "ta_paper_001",
          credential_slot_ref: "credslot://local-env/project_alpha/rp_paper_tradingnode/binance",
          credential_env_keys: ["BINANCE_API_KEY", "BINANCE_API_SECRET"],
          credential_values_resolved: true,
          tradingnode_config: { config_type: "TradingNodeConfig" },
          attached_strategy: { strategy_version_id: "strategy_001_v004", may_submit_order: false },
          lifecycle_events: [
            { status: "INITIALIZED", message: "accepted", timestamp: "2026-05-27T00:00:00Z", session_id: "exec_session_001" },
            { status: "RUNNING", message: "started", timestamp: "2026-05-27T00:00:01Z", session_id: "exec_session_001" },
            { status: "DISPOSED", message: "disposed", timestamp: "2026-05-27T00:01:00Z", session_id: "exec_session_001" },
          ],
          browser_credentials_allowed: false,
          credential_inputs_allowed: false,
          strategy_lane_coupled: false,
          live_trading_enabled: false,
          execution_authority: false,
          may_submit_order: false,
        }, { status: 202 });
      }
      throw new Error(`unexpected fetch ${method} ${url}`);
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<ExecutionLaneFeaturePanel />);

    expect(await screen.findByText("Feature visibility matrix")).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Credential variable 1"), { target: { value: "BINANCE_API_KEY" } });
    fireEvent.change(screen.getByLabelText("Credential value 1"), { target: { value: "test-binance-key" } });
    fireEvent.change(screen.getByLabelText("Credential variable 2"), { target: { value: "BINANCE_API_SECRET" } });
    fireEvent.change(screen.getByLabelText("Credential value 2"), { target: { value: "test-binance-secret" } });
    fireEvent.click(screen.getByRole("button", { name: "Save credential slot" }));
    await waitFor(() => expect(screen.getByText("Credential slot ready")).toBeInTheDocument());

    fireEvent.click(screen.getByRole("button", { name: "Wire paper profile" }));
    await waitFor(() => expect(screen.getByText("Runtime plan READY")).toBeInTheDocument());
    fireEvent.click(screen.getByRole("button", { name: "Queue paper command" }));
    await waitFor(() => expect(screen.getByText("Command queued: exec_cmd_paper_001")).toBeInTheDocument());

    fireEvent.click(screen.getByRole("button", { name: "Start Paper Session" }));
    await waitFor(() => expect(screen.getByText("Paper session: RUNNING")).toBeInTheDocument());
    expect(screen.getByText("runner_mode: contract_dry_run")).toBeInTheDocument();
    expect(screen.queryByText("test-binance-key")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Stop / Dispose" }));
    await waitFor(() => expect(screen.getByText("Paper session: DISPOSED")).toBeInTheDocument());
    expect(screen.queryByRole("button", { name: /submit order/i })).not.toBeInTheDocument();
  });

});
