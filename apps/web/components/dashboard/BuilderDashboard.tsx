"use client";

import { useState } from "react";
import {
  AuditOutlined,
  CheckCircleOutlined,
  CodeOutlined,
  ExperimentOutlined,
  PlayCircleOutlined,
  RobotOutlined,
  SafetyCertificateOutlined,
} from "@ant-design/icons";
import { Alert, Card, Col, Row, Space, Statistic, Steps, Tabs, Tag, Typography } from "antd";
import { AiStrategyCopilot } from "../ai-builder/AiStrategyCopilot";
import { BacktestLaunchPanel } from "../backtests/BacktestLaunchPanel";
import { ExecutionLaneFeaturePanel } from "../config/ExecutionLaneFeaturePanel";
import { PromotionRequestPanel } from "../promotions/PromotionRequestPanel";
import { StrategyBuilderWorkspace } from "../strategy-builder/StrategyBuilderWorkspace";
import { JobTerminal } from "../terminal/JobTerminal";

const workflowSteps = [
  {
    title: "Strategy Builder",
    content: "Natural language → guarded StrategySpec",
  },
  {
    title: "Backtest Center",
    content: "Select data and run BacktestNode evidence",
  },
  {
    title: "Execution Lane",
    content: "Promoted strategy → paper/live TradingNode gate",
  },
];

const workflowTrail =
  "Strategy Builder → Backtest Center → Execution Lane";

const mainSections = [
  {
    key: "strategy",
    title: "Strategy Builder",
    summary:
      "Prompt-first drafting, AI-generated StrategySpec, schema validation, block editing, and guardrails.",
    tag: "AI + StrategySpec",
  },
  {
    key: "backtest",
    title: "Backtest Center",
    summary:
      "Pick strategy/data/venue/instrument/range and trigger backend-owned BacktestNode replay evidence.",
    tag: "Historical replay",
  },
  {
    key: "execution",
    title: "Execution Lane",
    summary:
      "Decoupled paper/live lane using TradingNode profiles, server-side credential slots, and lifecycle controls.",
    tag: "Paper / live gated",
  },
];

export function BuilderDashboard() {
  const [activeSection, setActiveSection] = useState("strategy");

  return (
    <Space orientation="vertical" size="middle" className="builder-dashboard compact-dashboard product-workflow-dashboard">
      <Card className="dashboard-hero-card product-hero-card">
        <Row gutter={[20, 20]} align="middle">
          <Col xs={24} xl={15}>
            <Space orientation="vertical" size="middle">
              <Tag color="cyan" icon={<SafetyCertificateOutlined />}>
                Builder-only / no browser execution authority
              </Tag>
              <div>
                <Typography.Text className="hero-kicker">Command center</Typography.Text>
                <Typography.Title level={2}>Nautilus Builder</Typography.Title>
                <Typography.Title level={3} className="dashboard-entry-title">
                  Three-section operator workflow
                </Typography.Title>
                <Typography.Paragraph className="workflow-trail">
                  {workflowTrail}
                </Typography.Paragraph>
                <Typography.Paragraph>
                  Start with natural language, convert it to a validated StrategySpec,
                  prove it through a BacktestNode run, then move only promoted
                  versions into the decoupled paper/live execution lane.
                </Typography.Paragraph>
              </div>
              <Alert
                showIcon
                type="info"
                title="Keep strategy, backtest, and execution separate"
                description="Strategy drafting has no venue credentials, BacktestNode is historical evidence-only, and TradingNode controls stay behind backend risk gates plus manual approval."
              />
              <Space wrap>
                <button type="button" className="workflow-action-primary" onClick={() => setActiveSection("strategy")}>
                  Open Strategy Builder
                </button>
                <button type="button" onClick={() => setActiveSection("backtest")}>
                  Run BacktestNode
                </button>
                <button type="button" onClick={() => setActiveSection("execution")}>
                  Open Execution Lane
                </button>
                <Tag color="warning">Manual promotion before paper/live</Tag>
              </Space>
            </Space>
          </Col>
          <Col xs={24} xl={9}>
            <Row gutter={[10, 10]}>
              <Col span={12}>
                <Card size="small">
                  <Statistic title="Strategy lane" value="AI" prefix={<RobotOutlined />} />
                </Card>
              </Col>
              <Col span={12}>
                <Card size="small">
                  <Statistic title="Backtest lane" value="BT" prefix={<ExperimentOutlined />} />
                </Card>
              </Col>
              <Col span={12}>
                <Card size="small">
                  <Statistic title="Execution lane" value="TN" prefix={<PlayCircleOutlined />} />
                </Card>
              </Col>
              <Col span={12}>
                <Card size="small">
                  <Statistic title="Manual gates" value={1} prefix={<AuditOutlined />} />
                </Card>
              </Col>
              <Col span={24}>
                <Card size="small" title="Authority split">
                  <Typography.Text type="secondary">
                    Backtest uses BacktestNode; paper/live uses TradingNode via backend-owned sessions only.
                  </Typography.Text>
                </Card>
              </Col>
            </Row>
          </Col>
        </Row>
      </Card>

      <Card
        className="compact-workflow-card"
        size="small"
        title="Product flow"
        extra={<Tag color="green">StrategySpec guarded</Tag>}
      >
        <Typography.Paragraph className="workflow-trail">{workflowTrail}</Typography.Paragraph>
        <Steps size="small" current={mainSections.findIndex((section) => section.key === activeSection)} items={workflowSteps} />
      </Card>

      <Row gutter={[8, 8]} className="surface-overview compact-surface-overview product-section-cards">
        {mainSections.map((section) => (
          <Col xs={24} lg={8} key={section.key}>
            <Card
              size="small"
              className={activeSection === section.key ? "section-card-active" : undefined}
              onClick={() => setActiveSection(section.key)}
            >
              <Space orientation="vertical" size={4}>
                <Tag color={section.key === "execution" ? "purple" : section.key === "backtest" ? "gold" : "cyan"}>
                  {section.tag}
                </Tag>
                <Typography.Title level={2}>{section.title}</Typography.Title>
                <Typography.Paragraph>{section.summary}</Typography.Paragraph>
              </Space>
            </Card>
          </Col>
        ))}
      </Row>

      <Tabs
        className="operator-workspace-tabs product-main-tabs"
        activeKey={activeSection}
        onChange={setActiveSection}
        items={[
          {
            key: "strategy",
            label: "1. Strategy Builder",
            children: (
              <Space orientation="vertical" size="middle" className="main-section-stack">
                <Card
                  size="small"
                  title="Strategy Builder"
                  extra={<Tag color="gold">Natural language → StrategySpec</Tag>}
                >
                  <Row gutter={[12, 12]}>
                    <Col xs={24} xl={10}>
                      <AiStrategyCopilot />
                    </Col>
                    <Col xs={24} xl={14}>
                      <StrategyBuilderWorkspace />
                    </Col>
                  </Row>
                </Card>
                <Card size="small" title="Strategy lane guardrails" extra={<Tag icon={<CodeOutlined />} color="blue">Draft only</Tag>}>
                  <Typography.Paragraph>
                    AI output is advisory until the backend validates schema, forbidden-token policy, market data contract,
                    risk rules, and output mode. Strategy drafts do not carry browser credentials or runtime handles.
                  </Typography.Paragraph>
                </Card>
              </Space>
            ),
          },
          {
            key: "backtest",
            label: "2. Backtest Center",
            children: (
              <Space orientation="vertical" size="middle" className="main-section-stack">
                <Card
                  size="small"
                  title="Backtest Center"
                  extra={<Tag color="purple">BacktestNode historical replay</Tag>}
                >
                  <BacktestLaunchPanel />
                  <Typography.Paragraph className="terminal-line">
                    {JobTerminal()}
                  </Typography.Paragraph>
                </Card>
                <Card
                  size="small"
                  title="Manual promotion review"
                  extra={<Tag icon={<CheckCircleOutlined />} color="blue">Human gate</Tag>}
                >
                  <PromotionRequestPanel />
                </Card>
              </Space>
            ),
          },
          {
            key: "execution",
            label: "3. Execution Lane",
            children: (
              <Card
                size="small"
                title="Execution Lane"
                extra={<Tag color="red">TradingNode paper/live gated</Tag>}
              >
                <ExecutionLaneFeaturePanel />
              </Card>
            ),
          },
        ]}
      />
    </Space>
  );
}
