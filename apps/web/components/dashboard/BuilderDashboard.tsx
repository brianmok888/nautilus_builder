"use client";

import { useState } from "react";
import {
  CodeOutlined,
  ExperimentOutlined,
  PlayCircleOutlined,
  SafetyCertificateOutlined,
} from "@ant-design/icons";
import { Card, Row, Col, Space, Tag, Tabs, Typography } from "antd";
import { AiStrategyCopilot } from "../ai-builder/AiStrategyCopilot";
import { BacktestLaunchPanel } from "../backtests/BacktestLaunchPanel";
import { ExecutionLaneFeaturePanel } from "../config/ExecutionLaneFeaturePanel";
import { PromotionRequestPanel } from "../promotions/PromotionRequestPanel";
import { StrategyBuilderWorkspace } from "../strategy-builder/StrategyBuilderWorkspace";
import { JobTerminal } from "../terminal/JobTerminal";

const { Text, Paragraph, Title } = Typography;

export function BuilderDashboard() {
  const [activeSection, setActiveSection] = useState("strategy");

  return (
    <div className="builder-dashboard">
      {/* Compact header — one line of context, no repeated explanations */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 12,
          padding: "8px 0",
          flexWrap: "wrap",
        }}
      >
        <Title level={4} style={{ margin: 0 }}>
          Nautilus Builder
        </Title>
        <Tag color="cyan" icon={<SafetyCertificateOutlined />}>
          No browser execution authority
        </Tag>
        <Tag color="warning">Manual promotion before paper/live</Tag>
      </div>

      {/* Single tab bar — the entire UI */}
      <Tabs
        className="operator-workspace-tabs"
        activeKey={activeSection}
        onChange={setActiveSection}
        items={[
          {
            key: "strategy",
            label: (
              <Space size={4}>
                <CodeOutlined />
                Strategy Builder
              </Space>
            ),
            children: (
              <Row gutter={[16, 16]}>
                <Col xs={24} xl={10}>
                  <Card
                    size="small"
                    title="AI Draft"
                    extra={<Tag color="gold">Advisory only</Tag>}
                  >
                    <AiStrategyCopilot />
                  </Card>
                </Col>
                <Col xs={24} xl={14}>
                  <Space direction="vertical" size="middle" style={{ width: "100%" }}>
                    <Card size="small" title="StrategySpec Editor">
                      <StrategyBuilderWorkspace />
                    </Card>
                    <Card
                      size="small"
                      title="Guardrails"
                      extra={<Tag icon={<CodeOutlined />} color="blue">Draft only</Tag>}
                    >
                      <Paragraph type="secondary">
                        AI output is advisory until the backend validates schema,
                        forbidden-token policy, market data contract, risk rules, and
                        output mode. Strategy drafts do not carry browser credentials
                        or runtime handles.
                      </Paragraph>
                    </Card>
                  </Space>
                </Col>
              </Row>
            ),
          },
          {
            key: "backtest",
            label: (
              <Space size={4}>
                <ExperimentOutlined />
                Backtest Center
              </Space>
            ),
            children: (
              <Space direction="vertical" size="middle" style={{ width: "100%" }}>
                <Card
                  size="small"
                  title="BacktestNode Replay"
                  extra={<Tag color="purple">Historical evidence-only</Tag>}
                >
                  <BacktestLaunchPanel />
                  <Text type="secondary" style={{ display: "block", marginTop: 8 }}>
                    {JobTerminal()}
                  </Text>
                </Card>
                <Card
                  size="small"
                  title="Manual Promotion Review"
                  extra={<Tag color="blue">Human gate</Tag>}
                >
                  <PromotionRequestPanel />
                </Card>
              </Space>
            ),
          },
          {
            key: "execution",
            label: (
              <Space size={4}>
                <PlayCircleOutlined />
                Execution Lane
              </Space>
            ),
            children: (
              <Card
                size="small"
                title="Paper / Live TradingNode"
                extra={<Tag color="red">Backend-owned credentials</Tag>}
              >
                <ExecutionLaneFeaturePanel />
              </Card>
            ),
          },
        ]}
      />
    </div>
  );
}
