"use client";

import { useEffect, useMemo, useState } from "react";
import { Alert, Badge, Card, Col, Divider, Row, Space, Switch, Tag, Typography } from "antd";
import { fetchExecutionLaneStatus } from "../../lib/api";
import type { ExecutionLaneStatus } from "../../lib/types";

const fallbackStatus: ExecutionLaneStatus = {
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
};

function boolText(value: boolean): string {
  return value ? "true" : "false";
}

export function ExecutionLaneFeaturePanel() {
  const [status, setStatus] = useState<ExecutionLaneStatus>(fallbackStatus);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

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
  const preview = useMemo(
    () => ({
      mode: status.mode,
      venue_bindings: bindings,
      ui_features: features,
      strategy_lane_coupled: status.strategy_lane_coupled,
      may_submit_order: status.may_submit_order,
      credential_policy: "server-side credential slot only",
    }),
    [bindings, features, status.may_submit_order, status.mode, status.strategy_lane_coupled],
  );

  return (
    <section className="panel config-panel" aria-label="execution lane feature configuration">
      <Space orientation="vertical" size="middle" className="config-stack">
        <Alert
          showIcon
          type="warning"
          message="Execution lane feature flags are backend-owned"
          description="The UI can show or hide execution controls, but venue credentials and order authority stay server-side behind risk, reconciliation, manual approval, and credential-slot gates."
        />

        <Card title="Execution lane venue binding" loading={loading}>
          <Typography.Paragraph>
            Link each execution lane to an approved adapter venue before any paper
            or live controls are visible. Browser credential inputs allowed: false;
            server-side credential slot only.
          </Typography.Paragraph>
          <Row gutter={[12, 12]}>
            <Col xs={24} md={8}>
              <Card size="small" title="Adapter ID">
                {bindings.length === 0 ? (
                  <Typography.Text type="secondary">No active binding</Typography.Text>
                ) : (
                  <Space direction="vertical" size={4}>
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
                  <Space direction="vertical" size={4}>
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
                <Space direction="vertical" size={4}>
                  <Typography.Text>strategy lane coupled: {boolText(status.strategy_lane_coupled)}</Typography.Text>
                  <Typography.Text>may submit order: {boolText(status.may_submit_order)}</Typography.Text>
                  <Typography.Text>credential inputs allowed: false</Typography.Text>
                </Space>
              </Card>
            </Col>
          </Row>
        </Card>

        <Card title="Execution lane UI">
          <Row gutter={[12, 12]}>
            <Col xs={24} md={8}>
              <Space direction="vertical" size={4}>
                <Typography.Text strong>Execution lane UI</Typography.Text>
                <Switch checked={features.execution_lane_ui_enabled} disabled />
                <Badge status={features.execution_lane_ui_enabled ? "success" : "default"} text={`backend flag: ${boolText(features.execution_lane_ui_enabled)}`} />
              </Space>
            </Col>
            <Col xs={24} md={8}>
              <Space direction="vertical" size={4}>
                <Typography.Text strong>Paper controls</Typography.Text>
                <Switch checked={features.paper_controls_enabled} disabled />
                <Badge status={features.paper_controls_enabled ? "processing" : "default"} text={`simulated-only: ${boolText(features.paper_controls_enabled)}`} />
              </Space>
            </Col>
            <Col xs={24} md={8}>
              <Space direction="vertical" size={4}>
                <Typography.Text strong>Live controls</Typography.Text>
                <Switch checked={features.live_controls_enabled} disabled />
                <Badge status={features.live_controls_enabled ? "warning" : "default"} text={`requires live authority: ${boolText(features.live_controls_enabled)}`} />
              </Space>
            </Col>
          </Row>
          <Divider />
          <Typography.Paragraph type="secondary">
            server-side credential slot only; the web app never collects exchange
            secrets, passwords, or venue signing material.
          </Typography.Paragraph>
          {error ? <Alert type="error" showIcon message="Execution lane status unavailable" description={error} /> : null}
        </Card>

        <Card title="Execution feature preview" className="config-preview">
          <pre>{JSON.stringify(preview, null, 2)}</pre>
        </Card>
      </Space>
    </section>
  );
}
