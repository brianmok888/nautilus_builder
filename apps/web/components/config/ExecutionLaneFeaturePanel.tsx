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
  Space,
  Switch,
  Tag,
  Typography,
} from "antd";
import {
  fetchExecutionLaneRuntimePlan,
  fetchExecutionLaneStatus,
  registerExecutionLaneProfile,
} from "../../lib/api";
import type {
  ExecutionLaneRuntimePlan,
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

type PaperProfileDraft = {
  tenant_id: string;
  project_id: string;
  runtime_profile_id: string;
  profile_name: string;
  adapter_id: string;
  venue: string;
  venue_account_id: string;
};

const defaultProfileDraft: PaperProfileDraft = {
  tenant_id: "tenant_a",
  project_id: "project_alpha",
  runtime_profile_id: "rp_paper_tradingnode",
  profile_name: "Paper TradingNode lane",
  adapter_id: "BINANCE_PERP",
  venue: "BINANCE",
  venue_account_id: "SIM-BINANCE-001",
};

function boolText(value: boolean): string {
  return value ? "true" : "false";
}

function streamName(draft: PaperProfileDraft): string {
  return `builder.execution.commands.paper.${draft.project_id}.${draft.venue.toLowerCase()}`;
}

function profilePayload(draft: PaperProfileDraft): Record<string, unknown> {
  return {
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
}

export function ExecutionLaneFeaturePanel({ strategy }: { strategy?: { strategy_id: string; strategy_lineage_id?: string } | null }) {
  const [status, setStatus] = useState<ExecutionLaneStatus>(fallbackStatus);
  const [profileDraft, setProfileDraft] = useState<PaperProfileDraft>(defaultProfileDraft);
  const [runtimePlan, setRuntimePlan] = useState<ExecutionLaneRuntimePlan | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [action, setAction] = useState<"profile" | null>(null);

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
  const profilePreview = useMemo(() => profilePayload(profileDraft), [profileDraft]);
  const preview = useMemo(
    () => ({
      mode: status.mode,
      venue_bindings: bindings,
      ui_features: features,
      selected_strategy_id: strategy?.strategy_id ?? null,
      strategy_lane_coupled: status.strategy_lane_coupled,
      may_submit_order: status.may_submit_order,
      credential_policy: "server-side credential slot only",
      browser_runtime_actions: "disabled",
      runtime_plan: runtimePlan
        ? {
            readiness_status: runtimePlan.readiness_status,
            node_runtime: runtimePlan.node_runtime,
            runtime_label: runtimePlan.runtime_label,
            runtime_environment: runtimePlan.runtime_environment,
            may_submit_order: runtimePlan.may_submit_order,
          }
        : null,
    }),
    [bindings, features, runtimePlan, status.may_submit_order, status.mode, status.strategy_lane_coupled, strategy?.strategy_id],
  );

  function updateProfileField<K extends keyof PaperProfileDraft>(field: K, value: PaperProfileDraft[K]) {
    setProfileDraft((current) => ({ ...current, [field]: value }));
    setRuntimePlan(null);
  }

  async function refreshStatus(runtimeProfileId = profileDraft.runtime_profile_id) {
    const next = await fetchExecutionLaneStatus(runtimeProfileId);
    setStatus(next);
  }

  async function onWireProfile() {
    setAction("profile");
    setError(null);
    try {
      await registerExecutionLaneProfile(profilePreview);
      const plan = await fetchExecutionLaneRuntimePlan(profileDraft.runtime_profile_id);
      setRuntimePlan(plan);
      await refreshStatus(profileDraft.runtime_profile_id);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : String(caught));
    } finally {
      setAction(null);
    }
  }

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
          description="The UI can request backend-owned paper TradingNode profile visibility and runtime plans, but command construction, worker/session lifecycle, venue credentials, and order authority stay server-side behind risk, reconciliation, manual approval, and credential-slot gates."
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

        <Card title="Paper TradingNode visibility wire" size="small">
          <Typography.Paragraph type="secondary">
            Web wire: save a paper runtime profile and fetch the guarded TradingNode runtime plan.
            Backend services own command creation, worker execution, and session lifecycle; the browser only requests and observes.
          </Typography.Paragraph>
          <Form layout="vertical" className="form-grid">
            <Form.Item label="Runtime profile ID">
              <Input
                aria-label="Runtime profile ID"
                value={profileDraft.runtime_profile_id}
                onChange={(event) => updateProfileField("runtime_profile_id", event.target.value)}
              />
            </Form.Item>
            <Form.Item label="Adapter ID">
              <Input
                aria-label="Execution adapter ID"
                value={profileDraft.adapter_id}
                onChange={(event) => updateProfileField("adapter_id", event.target.value)}
              />
            </Form.Item>
            <Form.Item label="Venue">
              <Input
                aria-label="Execution venue"
                value={profileDraft.venue}
                onChange={(event) => updateProfileField("venue", event.target.value)}
              />
            </Form.Item>
            <Form.Item label="Venue account">
              <Input
                aria-label="Venue account"
                value={profileDraft.venue_account_id}
                onChange={(event) => updateProfileField("venue_account_id", event.target.value)}
              />
            </Form.Item>
          </Form>
          <Space wrap>
            <Button type="primary" loading={action === "profile"} onClick={onWireProfile}>
              Wire paper profile
            </Button>
            <Tag color="green">paper sandbox only</Tag>
            <Tag color="gold">backend action owner</Tag>
            <Tag color="blue">browser observe-only</Tag>
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
            server-side credential slot only; profile and runtime-plan payloads never carry raw exchange secrets,
            passwords, or venue signing material. Browser runtime actions are disabled.
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
