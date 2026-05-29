"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Alert,
  Badge,
  Button,
  Card,
  Col,
  Divider,
  Form,
  Input,
  Row,
  Select,
  Space,
  Switch,
  Tag,
  Typography,
} from "antd";
import {
  enqueueExecutionLaneCommand,
  fetchExecutionLaneRuntimePlan,
  fetchExecutionLaneStatus,
  registerExecutionLaneProfile,
  runExecutionLaneWorkerOnce,
  saveExecutionLaneCredentialSlot,
  startExecutionLanePaperSession,
  stopExecutionLaneSession,
} from "../../lib/api";
import type {
  ExecutionCredentialSlot,
  ExecutionLaneCommand,
  ExecutionLaneReport,
  ExecutionLaneRuntimePlan,
  ExecutionLaneSession,
  ExecutionLaneStatus,
} from "../../lib/types";

const fallbackStatus: ExecutionLaneStatus = {
  mode: "execution_lane",
  runtime_profile_id: null,
  profiles: 0,
  queued_commands: 0,
  claimed_commands: 0,
  reported_commands: 0,
  reports: 0,
  sessions: 0,
  running_sessions: 0,
  credential_slots: 0,
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
};

type PaperWireDraft = {
  tenant_id: string;
  project_id: string;
  runtime_profile_id: string;
  profile_name: string;
  adapter_id: string;
  venue: string;
  venue_account_id: string;
  instrument_id: string;
  side: "BUY" | "SELL";
  quantity: string;
  strategy_lineage_id: string;
  strategy_version_id: string;
};

type CredentialDraft = {
  requested_by: string;
  variable_1: string;
  value_1: string;
  variable_2: string;
  value_2: string;
};

const defaultWireDraft: PaperWireDraft = {
  tenant_id: "tenant_a",
  project_id: "project_alpha",
  runtime_profile_id: "rp_paper_tradingnode",
  profile_name: "Paper TradingNode lane",
  adapter_id: "BINANCE_PERP",
  venue: "BINANCE",
  venue_account_id: "SIM-BINANCE-001",
  instrument_id: "BTCUSDT-PERP.BINANCE",
  side: "BUY",
  quantity: "0.01",
  strategy_lineage_id: "lineage_ema_rsi",
  strategy_version_id: "strategy_001_v004",
};

const defaultCredentialDraft: CredentialDraft = {
  requested_by: "ops_user",
  variable_1: "",
  value_1: "",
  variable_2: "",
  value_2: "",
};

function boolText(value: boolean): string {
  return value ? "true" : "false";
}

function streamName(draft: PaperWireDraft): string {
  return `builder.execution.commands.paper.${draft.project_id}.${draft.venue.toLowerCase()}`;
}

function profilePayload(draft: PaperWireDraft, credentialSlotRef?: string): Record<string, unknown> {
  const payload: Record<string, unknown> = {
    tenant_id: draft.tenant_id,
    project_id: draft.project_id,
    runtime_profile_id: draft.runtime_profile_id,
    profile_name: draft.profile_name,
    lane_mode: "paper",
    enabled: true,
    paper_trading_enabled: true,
    adapter_id: draft.adapter_id,
    venue: draft.venue,
    venue_account_id: draft.venue_account_id,
    ui_enabled: true,
    paper_controls_enabled: true,
    live_controls_enabled: false,
    consumes_stream: streamName(draft),
  };
  if (credentialSlotRef) payload.credential_slot_ref = credentialSlotRef;
  return payload;
}

function commandPayload(draft: PaperWireDraft): Record<string, unknown> {
  return {
    tenant_id: draft.tenant_id,
    project_id: draft.project_id,
    runtime_profile_id: draft.runtime_profile_id,
    lane_mode: "paper",
    adapter_id: draft.adapter_id,
    venue: draft.venue,
    venue_account_id: draft.venue_account_id,
    trade_action_id: `ta_${draft.runtime_profile_id}`,
    source_event_id: `gate_evt_${draft.runtime_profile_id}`,
    idempotency_key: `gate_evt_${draft.runtime_profile_id}:ta_${draft.runtime_profile_id}`,
    strategy_lineage_id: draft.strategy_lineage_id,
    strategy_version_id: draft.strategy_version_id,
    order_intent: {
      side: draft.side,
      instrument_id: draft.instrument_id,
      quantity: draft.quantity,
    },
    risk_decision: {
      status: "approved",
      risk_profile_id: "risk_paper_default",
    },
  };
}

function credentialValues(draft: CredentialDraft): Record<string, string> {
  return Object.fromEntries(
    [
      [draft.variable_1, draft.value_1],
      [draft.variable_2, draft.value_2],
    ]
      .map(([key, value]) => [key.trim().toUpperCase(), value] as const)
      .filter(([key, value]) => key && value.trim()),
  );
}

function credentialPayload(wireDraft: PaperWireDraft, credentialDraft: CredentialDraft): Record<string, unknown> {
  return {
    tenant_id: wireDraft.tenant_id,
    project_id: wireDraft.project_id,
    runtime_profile_id: wireDraft.runtime_profile_id,
    adapter_id: wireDraft.adapter_id,
    venue: wireDraft.venue,
    lane_mode: "paper",
    requested_by: credentialDraft.requested_by,
    credential_values: credentialValues(credentialDraft),
  };
}

export function ExecutionLaneFeaturePanel() {
  const [status, setStatus] = useState<ExecutionLaneStatus>(fallbackStatus);
  const [wireDraft, setWireDraft] = useState<PaperWireDraft>(defaultWireDraft);
  const [credentialDraft, setCredentialDraft] = useState<CredentialDraft>(defaultCredentialDraft);
  const [credentialSlot, setCredentialSlot] = useState<ExecutionCredentialSlot | null>(null);
  const [runtimePlan, setRuntimePlan] = useState<ExecutionLaneRuntimePlan | null>(null);
  const [command, setCommand] = useState<ExecutionLaneCommand | null>(null);
  const [workerReport, setWorkerReport] = useState<ExecutionLaneReport | null>(null);
  const [session, setSession] = useState<ExecutionLaneSession | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [action, setAction] = useState<"credential" | "profile" | "command" | "worker" | "start-session" | "stop-session" | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function loadStatus() {
      try {
        const payload = await fetchExecutionLaneStatus();
        if (!cancelled) {
          setStatus(payload);
          setError(null);
        }
      } catch (caught) {
        if (!cancelled) {
          setError(caught instanceof Error ? caught.message : String(caught));
          setStatus(fallbackStatus);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    loadStatus();
    return () => {
      cancelled = true;
    };
  }, []);

  const features = status.ui_features ?? fallbackStatus.ui_features;
  const bindings = status.venue_bindings ?? [];
  const profilePreview = useMemo(() => profilePayload(wireDraft, credentialSlot?.credential_slot_ref), [credentialSlot?.credential_slot_ref, wireDraft]);
  const commandPreview = useMemo(() => commandPayload(wireDraft), [wireDraft]);
  const credentialPreview = useMemo(() => credentialPayload(wireDraft, credentialDraft), [credentialDraft, wireDraft]);
  const preview = useMemo(
    () => ({
      mode: status.mode,
      venue_bindings: bindings,
      ui_features: features,
      strategy_lane_coupled: status.strategy_lane_coupled,
      may_submit_order: status.may_submit_order,
      credential_policy: "server-side credential slot only",
      credential_slot_ref: credentialSlot?.credential_slot_ref ?? null,
      credential_slot_redacted_keys: credentialSlot?.redacted_keys ?? [],
      runtime_plan: runtimePlan
        ? {
            readiness_status: runtimePlan.readiness_status,
            node_runtime: runtimePlan.node_runtime,
            runtime_label: runtimePlan.runtime_label,
            runtime_environment: runtimePlan.runtime_environment,
            may_submit_order: runtimePlan.may_submit_order,
          }
        : null,
      command_id: command?.command_id ?? null,
      worker_report_id: workerReport?.report_id ?? null,
      session_id: session?.session_id ?? null,
      session_status: session?.lifecycle_status ?? null,
    }),
    [bindings, command, credentialSlot, features, runtimePlan, session, status.may_submit_order, status.mode, status.strategy_lane_coupled, workerReport],
  );

  function updateWireField<K extends keyof PaperWireDraft>(field: K, value: PaperWireDraft[K]) {
    setWireDraft((current) => ({ ...current, [field]: value }));
    setRuntimePlan(null);
    setCommand(null);
    setWorkerReport(null);
    setSession(null);
    setCredentialSlot(null);
  }

  async function refreshStatus(runtimeProfileId = wireDraft.runtime_profile_id) {
    const next = await fetchExecutionLaneStatus(runtimeProfileId);
    setStatus(next);
  }

  function updateCredentialField<K extends keyof CredentialDraft>(field: K, value: CredentialDraft[K]) {
    setCredentialDraft((current) => ({ ...current, [field]: value }));
    setCredentialSlot(null);
    setRuntimePlan(null);
    setCommand(null);
    setWorkerReport(null);
    setSession(null);
  }

  async function onSaveCredentialSlot() {
    setAction("credential");
    setError(null);
    setRuntimePlan(null);
    setCommand(null);
    setWorkerReport(null);
    setSession(null);
    try {
      const slot = await saveExecutionLaneCredentialSlot(credentialPreview as Parameters<typeof saveExecutionLaneCredentialSlot>[0]);
      setCredentialSlot(slot);
      setCredentialDraft((current) => ({ ...current, value_1: "", value_2: "" }));
      await refreshStatus(wireDraft.runtime_profile_id);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : String(caught));
    } finally {
      setAction(null);
    }
  }

  async function onWireProfile() {
    setAction("profile");
    setError(null);
    setWorkerReport(null);
    setSession(null);
    try {
      await registerExecutionLaneProfile(profilePreview);
      const plan = await fetchExecutionLaneRuntimePlan(wireDraft.runtime_profile_id);
      setRuntimePlan(plan);
      await refreshStatus(wireDraft.runtime_profile_id);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : String(caught));
    } finally {
      setAction(null);
    }
  }

  async function onQueueCommand() {
    setAction("command");
    setError(null);
    setWorkerReport(null);
    setSession(null);
    try {
      const queued = await enqueueExecutionLaneCommand(commandPreview);
      setCommand(queued);
      const plan = await fetchExecutionLaneRuntimePlan(wireDraft.runtime_profile_id, queued.command_id);
      setRuntimePlan(plan);
      await refreshStatus(wireDraft.runtime_profile_id);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : String(caught));
    } finally {
      setAction(null);
    }
  }

  async function onRunWorkerPlan() {
    setAction("worker");
    setError(null);
    try {
      const report = await runExecutionLaneWorkerOnce({
        runtime_profile_id: wireDraft.runtime_profile_id,
        worker_id: "web_execution_worker",
      });
      setWorkerReport(report);
      await refreshStatus(wireDraft.runtime_profile_id);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : String(caught));
    } finally {
      setAction(null);
    }
  }



  async function onStartPaperSession() {
    if (!command?.command_id) return;
    setAction("start-session");
    setError(null);
    try {
      const started = await startExecutionLanePaperSession({
        runtime_profile_id: wireDraft.runtime_profile_id,
        command_id: command.command_id,
        worker_id: "web_execution_worker",
        project_id: wireDraft.project_id,
      });
      setSession(started);
      await refreshStatus(wireDraft.runtime_profile_id);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : String(caught));
    } finally {
      setAction(null);
    }
  }

  async function onStopPaperSession() {
    if (!session?.session_id) return;
    setAction("stop-session");
    setError(null);
    try {
      const stopped = await stopExecutionLaneSession(session.session_id, { worker_id: "web_execution_worker" });
      setSession(stopped);
      await refreshStatus(wireDraft.runtime_profile_id);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : String(caught));
    } finally {
      setAction(null);
    }
  }

  const canSaveCredentialSlot = Object.keys(credentialValues(credentialDraft)).length > 0;
  const canQueue = Boolean(runtimePlan && runtimePlan.readiness_status === "READY");
  const canRunWorker = Boolean(command?.command_id);
  const canStartPaperSession = Boolean(command?.command_id && credentialSlot?.credential_slot_ref && runtimePlan?.readiness_status === "READY");
  const canStopPaperSession = Boolean(session?.session_id && session.lifecycle_status === "RUNNING");

  return (
    <section className="panel config-panel" aria-label="execution lane feature configuration">
      <Space orientation="vertical" size="middle" className="config-stack">
        <div>
          <Typography.Text className="hero-kicker">Execution Lane</Typography.Text>
          <Typography.Title level={3}>Feature visibility matrix</Typography.Title>
          <Typography.Paragraph type="secondary">
            Venue binding, paper controls visibility only, live controls visibility only, and no browser runtime authority.
          </Typography.Paragraph>
        </div>

        <Alert
          showIcon
          type="warning"
          title="Execution lane feature flags are backend-owned"
          description="The UI can wire paper TradingNode plans through backend contracts, but venue credentials and order authority stay server-side behind risk, reconciliation, manual approval, and credential-slot gates."
        />

        <Card title="Venue binding" loading={loading}>
          <Typography.Paragraph>
            Execution lane venue binding links each execution lane to an approved adapter venue before any paper
            or live controls are visible. Browser credential inputs allowed: false;
            server-side credential slot only.
          </Typography.Paragraph>
          <Row gutter={[12, 12]}>
            <Col xs={24} md={8}>
              <Card size="small" title="Adapter ID">
                {bindings.length === 0 ? (
                  <Typography.Text type="secondary">No active binding</Typography.Text>
                ) : (
                  <Space orientation="vertical" size={4}>
                    {bindings.map((binding) => (
                      <Tag key={`${binding.runtime_profile_id}:${binding.adapter_id}`} color="blue">
                        {binding.adapter_id}
                      </Tag>
                    ))}
                  </Space>
                )}
              </Card>
            </Col>
            <Col xs={24} md={8}>
              <Card size="small" title="Venue">
                {bindings.length === 0 ? (
                  <Typography.Text type="secondary">Awaiting backend profile</Typography.Text>
                ) : (
                  <Space orientation="vertical" size={4}>
                    {bindings.map((binding) => (
                      <Tag key={`${binding.runtime_profile_id}:${binding.venue}`} color="cyan">
                        {binding.venue}
                        {binding.venue_account_id ? ` · ${binding.venue_account_id}` : ""}
                      </Tag>
                    ))}
                  </Space>
                )}
              </Card>
            </Col>
            <Col xs={24} md={8}>
              <Card size="small" title="Lane safety">
                <Space orientation="vertical" size={4}>
                  <Typography.Text>strategy lane coupled: {boolText(status.strategy_lane_coupled)}</Typography.Text>
                  <Typography.Text>may submit order: {boolText(status.may_submit_order)}</Typography.Text>
                  <Typography.Text>credential inputs allowed: false</Typography.Text>
                </Space>
              </Card>
            </Col>
          </Row>
        </Card>



        <Card title="Paper TradingNode wire" size="small">
          <Typography.Paragraph type="secondary">
            Full web wire: save a paper runtime profile, fetch the guarded TradingNode runtime plan,
            enqueue a paper command, then ask the backend worker seam to emit a runtime-plan report.
            The browser does not receive shell access, raw credentials, or live order authority.
          </Typography.Paragraph>
          <Form layout="vertical" className="form-grid">
            <Form.Item label="Runtime profile ID">
              <Input
                aria-label="Runtime profile ID"
                value={wireDraft.runtime_profile_id}
                onChange={(event) => updateWireField("runtime_profile_id", event.target.value)}
              />
            </Form.Item>
            <Form.Item label="Adapter ID">
              <Input
                aria-label="Execution adapter ID"
                value={wireDraft.adapter_id}
                onChange={(event) => updateWireField("adapter_id", event.target.value)}
              />
            </Form.Item>
            <Form.Item label="Venue">
              <Input
                aria-label="Execution venue"
                value={wireDraft.venue}
                onChange={(event) => updateWireField("venue", event.target.value)}
              />
            </Form.Item>
            <Form.Item label="Venue account">
              <Input
                aria-label="Venue account"
                value={wireDraft.venue_account_id}
                onChange={(event) => updateWireField("venue_account_id", event.target.value)}
              />
            </Form.Item>
            <Form.Item label="Instrument">
              <Input
                aria-label="Execution instrument"
                value={wireDraft.instrument_id}
                onChange={(event) => updateWireField("instrument_id", event.target.value)}
              />
            </Form.Item>
            <Form.Item label="Side">
              <Select
                aria-label="Execution side"
                value={wireDraft.side}
                options={[{ value: "BUY", label: "BUY" }, { value: "SELL", label: "SELL" }]}
                onChange={(value) => updateWireField("side", value)}
              />
            </Form.Item>
            <Form.Item label="Quantity">
              <Input
                aria-label="Execution quantity"
                value={wireDraft.quantity}
                onChange={(event) => updateWireField("quantity", event.target.value)}
              />
            </Form.Item>
            <Form.Item label="Strategy version">
              <Input
                aria-label="Execution strategy version"
                value={wireDraft.strategy_version_id}
                onChange={(event) => updateWireField("strategy_version_id", event.target.value)}
              />
            </Form.Item>
          </Form>
          <Space wrap>
            <Button type="primary" loading={action === "profile"} onClick={onWireProfile}>
              Wire paper profile
            </Button>
            <Button disabled={!canQueue} loading={action === "command"} onClick={onQueueCommand}>
              Queue paper command
            </Button>
            <Button disabled={!canRunWorker} loading={action === "worker"} onClick={onRunWorkerPlan}>
              Run backend worker plan
            </Button>
            <Button disabled={!canStartPaperSession} loading={action === "start-session"} onClick={onStartPaperSession}>
              Start Paper Session
            </Button>
            <Button danger disabled={!canStopPaperSession} loading={action === "stop-session"} onClick={onStopPaperSession}>
              Stop / Dispose
            </Button>
            <Tag color="green">paper sandbox only</Tag>
            <Tag color="gold">backend worker only</Tag>
          </Space>
        </Card>

        {runtimePlan ? (
          <Card title={`Runtime plan ${runtimePlan.readiness_status}`} size="small" aria-label="execution runtime plan">
            <Row gutter={[12, 12]}>
              <Col xs={24} md={12}>
                <Space orientation="vertical" size={4}>
                  <Typography.Text>node_runtime: {runtimePlan.node_runtime}</Typography.Text>
                  <Typography.Text>{runtimePlan.runtime_label}</Typography.Text>
                  <Typography.Text>runtime_environment: {runtimePlan.runtime_environment}</Typography.Text>
                  <Typography.Text>future_runtime: {runtimePlan.future_runtime}</Typography.Text>
                  <Typography.Text>credential_slot_ref: {runtimePlan.credential_slot_ref ?? "none"}</Typography.Text>
                </Space>
              </Col>
              <Col xs={24} md={12}>
                <Space orientation="vertical" size={4}>
                  <Typography.Text>may submit order: {boolText(runtimePlan.may_submit_order)}</Typography.Text>
                  <Typography.Text>browser credentials allowed: {boolText(runtimePlan.browser_credentials_allowed)}</Typography.Text>
                  <Typography.Text>credential inputs allowed: {boolText(runtimePlan.credential_inputs_allowed)}</Typography.Text>
                  <Typography.Text>reconciliation: {boolText(Boolean((runtimePlan.config_contract.exec_engine as { reconciliation?: boolean } | undefined)?.reconciliation))}</Typography.Text>
                </Space>
              </Col>
            </Row>
            {runtimePlan.blocked_reasons.length ? (
              <Alert showIcon type="warning" title={`Blocked gates: ${runtimePlan.blocked_reasons.join(", ")}`} />
            ) : null}
          </Card>
        ) : null}

        {command ? (
          <Alert
            showIcon
            type="success"
            title={`Command queued: ${command.command_id}`}
            description="The command is queued for the backend execution-lane worker; the browser still cannot start a venue process or submit orders."
          />
        ) : null}



        {session ? (
          <Card title={`Paper session: ${session.lifecycle_status}`} size="small" aria-label="execution paper session">
            <Row gutter={[12, 12]}>
              <Col xs={24} md={12}>
                <Space orientation="vertical" size={4}>
                  <Typography.Text>session_id: {session.session_id}</Typography.Text>
                  <Typography.Text>runner_mode: {session.runner_mode}</Typography.Text>
                  <Typography.Text>runtime_environment: {session.runtime_environment}</Typography.Text>
                  <Typography.Text>credential_slot_ref: {session.credential_slot_ref}</Typography.Text>
                  <Typography.Text>credential keys: {session.credential_env_keys.join(", ")}</Typography.Text>
                </Space>
              </Col>
              <Col xs={24} md={12}>
                <Space orientation="vertical" size={4}>
                  <Typography.Text>config: {String(session.tradingnode_config.config_type ?? "TradingNodeConfig")}</Typography.Text>
                  <Typography.Text>strategy version: {String(session.attached_strategy.strategy_version_id ?? session.strategy_version_id)}</Typography.Text>
                  <Typography.Text>may submit order: {boolText(session.may_submit_order)}</Typography.Text>
                  <Typography.Text>browser credentials allowed: {boolText(session.browser_credentials_allowed)}</Typography.Text>
                </Space>
              </Col>
            </Row>
            <Divider />
            <Space wrap>
              {session.lifecycle_events.map((event) => (
                <Tag key={`${event.status}:${event.timestamp}`} color={event.status === "RUNNING" ? "green" : event.status === "DISPOSED" ? "purple" : "blue"}>
                  {event.status}
                </Tag>
              ))}
            </Space>
          </Card>
        ) : null}

        {workerReport ? (
          <Card title={`Worker report: ${workerReport.report_type}`} size="small" aria-label="execution worker report">
            <Space orientation="vertical" size={4}>
              <Typography.Text>report_id: {workerReport.report_id}</Typography.Text>
              <Typography.Text>command_id: {workerReport.command_id}</Typography.Text>
              <Typography.Text>instrument: {workerReport.instrument_id}</Typography.Text>
              <Typography.Text>strategy lane coupled: {boolText(workerReport.strategy_lane_coupled)}</Typography.Text>
            </Space>
          </Card>
        ) : null}

        <Card title="Execution lane UI">
          <Row gutter={[12, 12]}>
            <Col xs={24} md={8}>
              <Space orientation="vertical" size={4}>
                <Typography.Text strong>Execution lane UI</Typography.Text>
                <Switch checked={features.execution_lane_ui_enabled} disabled />
                <Badge status={features.execution_lane_ui_enabled ? "success" : "default"} text={`backend flag: ${boolText(features.execution_lane_ui_enabled)}`} />
              </Space>
            </Col>
            <Col xs={24} md={8}>
              <Space orientation="vertical" size={4}>
                <Typography.Text strong>Paper controls visibility only</Typography.Text>
                <Switch checked={features.paper_controls_enabled} disabled />
                <Badge status={features.paper_controls_enabled ? "processing" : "default"} text={`simulated-only: ${boolText(features.paper_controls_enabled)}`} />
              </Space>
            </Col>
            <Col xs={24} md={8}>
              <Space orientation="vertical" size={4}>
                <Typography.Text strong>Live controls visibility only</Typography.Text>
                <Switch checked={features.live_controls_enabled} disabled />
                <Badge status={features.live_controls_enabled ? "warning" : "default"} text={`requires live authority: ${boolText(features.live_controls_enabled)}`} />
              </Space>
            </Col>
          </Row>
          <Divider />
          <Typography.Paragraph type="secondary">
            server-side credential slot only; profile, command, worker report, and runtime-plan payloads never
            carry raw exchange secrets, passwords, or venue signing material.
          </Typography.Paragraph>
          {error ? <Alert type="error" showIcon title="Execution lane request failed" description={error} /> : null}
        </Card>

        <Card title="Execution feature preview" className="config-preview">
          <pre>{JSON.stringify(preview, null, 2)}</pre>
        </Card>
      </Space>
    </section>
  );
}
