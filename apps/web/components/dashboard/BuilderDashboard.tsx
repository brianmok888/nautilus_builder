"use client";

import { useState } from "react";
import {
  CodeOutlined,
  ExperimentOutlined,
  PlayCircleOutlined,
  SafetyCertificateOutlined,
} from "@ant-design/icons";
import { Button, Card, Row, Col, Space, Tag, Typography } from "antd";
import { AiStrategyCopilot } from "../ai-builder/AiStrategyCopilot";
import { BacktestLaunchPanel } from "../backtests/BacktestLaunchPanel";
import { ExecutionLaneFeaturePanel } from "../config/ExecutionLaneFeaturePanel";
import { PromotionRequestPanel } from "../promotions/PromotionRequestPanel";
import { StrategyBuilderWorkspace } from "../strategy-builder/StrategyBuilderWorkspace";
import { JobTerminal } from "../terminal/JobTerminal";

const { Text, Paragraph, Title } = Typography;

const steps = [
  {
    key: "strategy",
    num: 1,
    icon: <CodeOutlined />,
    title: "Strategy Builder",
    subtitle: "AI draft → validated StrategySpec",
  },
  {
    key: "backtest",
    num: 2,
    icon: <ExperimentOutlined />,
    title: "Backtest Center",
    subtitle: "Historical replay evidence",
  },
  {
    key: "execution",
    num: 3,
    icon: <PlayCircleOutlined />,
    title: "Execution Lane",
    subtitle: "Paper / live TradingNode gate",
  },
] as const;

export function BuilderDashboard() {
  const [activeSection, setActiveSection] = useState("strategy");

  return (
    <div className="builder-dashboard">
      {/* Compact header */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 12,
          padding: "8px 0 4px",
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

      {/* 1-2-3 flow buttons */}
      <div
        style={{
          display: "flex",
          gap: 12,
          padding: "12px 0",
        }}
      >
        {steps.map((step) => {
          const active = activeSection === step.key;
          return (
            <Button
              key={step.key}
              type={active ? "primary" : "default"}
              size="large"
              onClick={() => setActiveSection(step.key)}
              style={{
                flex: 1,
                height: "auto",
                padding: "12px 16px",
                display: "flex",
                alignItems: "center",
                gap: 10,
                textAlign: "left",
                borderColor: active ? undefined : "var(--ant-color-border)",
              }}
            >
              <span
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  justifyContent: "center",
                  width: 32,
                  height: 32,
                  borderRadius: "50%",
                  fontSize: 18,
                  fontWeight: 700,
                  flexShrink: 0,
                  background: active
                    ? "rgba(255,255,255,0.2)"
                    : "var(--ant-color-bg-container)",
                  color: active
                    ? "#fff"
                    : "var(--ant-color-primary)",
                }}
              >
                {step.num}
              </span>
              <span>
                <div style={{ fontWeight: 600, fontSize: 14, lineHeight: "20px" }}>
                  {step.icon} {step.title}
                </div>
                <div style={{ fontSize: 12, opacity: 0.75, lineHeight: "16px" }}>
                  {step.subtitle}
                </div>
              </span>
            </Button>
          );
        })}
      </div>

      {/* Content panels */}
      <div style={{ marginTop: 8 }}>
        {activeSection === "strategy" && (
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
        )}

        {activeSection === "backtest" && (
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
        )}

        {activeSection === "execution" && (
          <Card
            size="small"
            title="Paper / Live TradingNode"
            extra={<Tag color="red">Backend-owned credentials</Tag>}
          >
            <ExecutionLaneFeaturePanel />
          </Card>
        )}
      </div>
    </div>
  );
}
