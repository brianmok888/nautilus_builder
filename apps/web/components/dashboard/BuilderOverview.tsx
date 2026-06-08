"use client";

import {
  CheckCircleOutlined,
  DatabaseOutlined,
  ExperimentOutlined,
  SafetyCertificateOutlined,
} from "@ant-design/icons";
import { Descriptions, Space, Tag, Typography } from "antd";
import { DashboardCard } from "../ui/DashboardCard";
import { MetricCard } from "../ui/MetricCard";

export function BuilderOverview() {
  return (
    <Space orientation="vertical" size="middle" style={{ width: "100%" }} aria-label="builder overview">
      <div className="nb-dashboard-grid nb-dashboard-grid-4">
        <MetricCard
          label="Mode"
          value="Builder-only mode"
          icon={<SafetyCertificateOutlined />}
          helper="No live order submission"
          tone="green"
        />
        <MetricCard
          label="Evidence"
          value="Backtest evidence"
          icon={<ExperimentOutlined />}
          helper="Historical evidence-only"
          tone="purple"
        />
        <MetricCard
          label="Authority"
          value="may_submit_order: false"
          icon={<CheckCircleOutlined />}
          helper="Execution authority remains external"
          tone="blue"
        />
        <MetricCard
          label="Browser"
          value="browser_credentials: false"
          icon={<DatabaseOutlined />}
          helper="Credentials stay backend-owned"
          tone="neutral"
        />
      </div>

      <DashboardCard
        title="Workspace Overview"
        subtitle="A read-only summary of Builder modules and the evidence path before any external promotion review."
        actions={<Tag color="green">Builder-only mode</Tag>}
      >
        <Descriptions column={{ xs: 1, md: 2 }} size="small" bordered>
          <Descriptions.Item label="Strategy Builder">
            Draft and validate StrategySpec artifacts before replay.
          </Descriptions.Item>
          <Descriptions.Item label="Backtest Center">
            Build historical replay manifests and collect evidence.
          </Descriptions.Item>
          <Descriptions.Item label="Results">
            Review observational metrics, artifacts, and report sections.
          </Descriptions.Item>
          <Descriptions.Item label="Safety boundary">
            No live order submission from the browser.
          </Descriptions.Item>
        </Descriptions>
      </DashboardCard>

      <DashboardCard
        title="Evidence data view"
        subtitle="Current Builder safety posture shown before entering a specific workflow lane."
        actions={<Tag color="blue">Historical evidence-only</Tag>}
      >
        <Space wrap>
          <Tag color="gold">may_submit_order: false</Tag>
          <Tag color="blue">browser_credentials: false</Tag>
          <Tag color="purple">Backtest evidence</Tag>
          <Tag color="green">No live order submission</Tag>
        </Space>
        <Typography.Paragraph type="secondary" style={{ marginTop: 12, marginBottom: 0 }}>
          Use Strategy Builder for draft and validation work, Backtest Center for replay evidence,
          and Results for observational reports.
        </Typography.Paragraph>
      </DashboardCard>
    </Space>
  );
}
