"use client";

import {
  AuditOutlined,
  CheckCircleOutlined,
  CodeOutlined,
  ExperimentOutlined,
  RobotOutlined,
  SafetyCertificateOutlined,
} from "@ant-design/icons";
import { Alert, Card, Col, Row, Space, Statistic, Steps, Tabs, Tag, Typography } from "antd";
import { AiStrategyCopilot } from "../ai-builder/AiStrategyCopilot";
import { PromotionRequestPanel } from "../promotions/PromotionRequestPanel";
import { StrategyBuilderWorkspace } from "../strategy-builder/StrategyBuilderWorkspace";
import { JobTerminal } from "../terminal/JobTerminal";

const workflowSteps = [
  { title: "Prompt", content: "Describe strategy intent" },
  { title: "StrategySpec", content: "AI drafts safe JSON" },
  { title: "Validate", content: "validate_strategy_spec()" },
  { title: "Backtest", content: "Nautilus replay evidence" },
  { title: "Manual promotion", content: "Human gate only" },
];

export function BuilderDashboard() {
  return (
    <Space orientation="vertical" size="middle" className="builder-dashboard compact-dashboard">
      <Card className="dashboard-hero-card">
        <Row gutter={[24, 24]} align="middle">
          <Col xs={24} xl={15}>
            <Space orientation="vertical" size="middle">
              <Tag color="cyan" icon={<SafetyCertificateOutlined />}>
                Builder-only / observational runtime
              </Tag>
              <div>
                <Typography.Title level={2}>Nautilus Builder</Typography.Title>
                <Typography.Paragraph>
                  Draft StrategySpecs, validate market data profiles, inspect
                  backtest evidence, and request safe shadow promotion without
                  granting the web UI live order authority.
                </Typography.Paragraph>
              </div>
              <Alert
                showIcon
                type="info"
                title="No live trading authority in this UI"
                description="AI output is advisory, StrategySpec drafts require backend validation, and promotion remains manual."
              />
              <Space wrap>
                <Tag color="blue" icon={<RobotOutlined />}>Start with AI prompt tab</Tag>
                <Tag color="warning">Requires validation before backtest</Tag>
              </Space>
            </Space>
          </Col>
          <Col xs={24} xl={9}>
            <Row gutter={[12, 12]}>
              <Col span={12}>
                <Card size="small">
                  <Statistic title="Drafts" value={1} prefix={<CodeOutlined />} />
                </Card>
              </Col>
              <Col span={12}>
                <Card size="small">
                  <Statistic title="Backtests" value={1} prefix={<ExperimentOutlined />} />
                </Card>
              </Col>
              <Col span={12}>
                <Card size="small">
                  <Statistic title="AI cycles" value={1} prefix={<RobotOutlined />} />
                </Card>
              </Col>
              <Col span={12}>
                <Card size="small">
                  <Statistic title="Manual gates" value={1} prefix={<AuditOutlined />} />
                </Card>
              </Col>
            </Row>
          </Col>
        </Row>
      </Card>

      <Card className="compact-workflow-card" size="small" title="Prompt-first workflow" extra={<Tag color="green">signal_preview_only</Tag>}>
        <Steps size="small" current={0} items={workflowSteps} />
      </Card>

      <Row gutter={[8, 8]} className="surface-overview compact-surface-overview">
        <Col xs={24} lg={6}>
          <Card size="small">
            <Typography.Title level={2}>Strategy draft authoring</Typography.Title>
            <Typography.Paragraph>Build StrategySpec drafts from blocks, market profiles, and AI suggestions.</Typography.Paragraph>
          </Card>
        </Col>
        <Col xs={24} lg={6}>
          <Card size="small">
            <Typography.Title level={2}>Observational runtime console</Typography.Title>
            <Typography.Paragraph>Inspect job state and request cancellation without exposing a shell.</Typography.Paragraph>
          </Card>
        </Col>
        <Col xs={24} lg={6}>
          <Card size="small">
            <Typography.Title level={2}>Advisory AI drafting</Typography.Title>
            <Typography.Paragraph>Turn operator prompts into validated StrategySpec candidates.</Typography.Paragraph>
            <Typography.Paragraph>ai_thread_id and improvement_cycle_id are required lane identifiers.</Typography.Paragraph>
          </Card>
        </Col>
        <Col xs={24} lg={6}>
          <Card size="small">
            <Typography.Title level={2}>Safe promotion request</Typography.Title>
            <Typography.Paragraph>Prepare manual promotion evidence after backtest review.</Typography.Paragraph>
            <Typography.Paragraph>approval_state: manual_approval_pending</Typography.Paragraph>
            <Typography.Paragraph>may_submit_order: false</Typography.Paragraph>
            <Typography.Paragraph>may_create_trade_action: false</Typography.Paragraph>
          </Card>
        </Col>
      </Row>

      <Tabs
        className="operator-workspace-tabs"
        defaultActiveKey="ai"
        items={[
          {
            key: "ai",
            label: "1. AI prompt",
            children: (
              <Card size="small" title="Advisory AI drafting" extra={<Tag color="gold">Advisory</Tag>}>
                <AiStrategyCopilot />
              </Card>
            ),
          },
          {
            key: "builder",
            label: "2. StrategySpec",
            children: (
              <Card
                size="small"
                title="Strategy draft authoring"
                extra={<Tag color="green">Draft only</Tag>}
              >
                <StrategyBuilderWorkspace />
              </Card>
            ),
          },
          {
            key: "runtime",
            label: "3. Runtime",
            children: (
              <Card
                size="small"
                title="Observational runtime console"
                extra={<Tag color="gold">Observational</Tag>}
              >
                <Typography.Paragraph className="terminal-line">
                  {JobTerminal()}
                </Typography.Paragraph>
              </Card>
            ),
          },
          {
            key: "promotion",
            label: "4. Promotion",
            children: (
              <Card
                size="small"
                title="Safe promotion request"
                extra={<Tag icon={<CheckCircleOutlined />} color="blue">Manual gate</Tag>}
              >
                <PromotionRequestPanel />
              </Card>
            ),
          },
        ]}
      />
    </Space>
  );
}
