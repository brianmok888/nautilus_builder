"use client";

import { useEffect, useState } from "react";
import {
  CodeOutlined,
  ExperimentOutlined,
  PlayCircleOutlined,
} from "@ant-design/icons";
import { useRouter } from "next/navigation";
import { Row, Col, Space, Tag, Typography } from "antd";
import { AiStrategyCopilot } from "../ai-builder/AiStrategyCopilot";
import { BacktestLaunchPanel } from "../backtests/BacktestLaunchPanel";
import { ExecutionLaneFeaturePanel } from "../config/ExecutionLaneFeaturePanel";
import { PromotionRequestPanel } from "../promotions/PromotionRequestPanel";
import { LaneStrategyTable } from "../strategy-builder/LaneStrategyTable";
import { StrategySpecEditor } from "../strategy-builder/StrategySpecEditor";
import { JobTerminal } from "../terminal/JobTerminal";
import { DashboardCard } from "../ui/DashboardCard";
import { WorkflowSteps, type WorkflowStep } from "../ui/WorkflowSteps";
import type { StrategySummary } from "../../lib/types";

const { Text, Paragraph } = Typography;

const steps: WorkflowStep[] = [
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
    subtitle: "Spec review → historical replay evidence",
  },
  {
    key: "execution",
    num: 3,
    icon: <PlayCircleOutlined />,
    title: "Execution Lane",
    subtitle: "Paper / live TradingNode gate",
  },
];

export function BuilderDashboard({
  initialTab = "strategy",
}: {
  initialTab?: string;
}) {
  const [activeSection, setActiveSection] = useState(initialTab);
  const [selectedStrategy, setSelectedStrategy] =
    useState<StrategySummary | null>(null);

  const router = useRouter();

  useEffect(() => {
    setActiveSection(initialTab);
  }, [initialTab]);

  function switchTab(key: string) {
    setActiveSection(key);
    setSelectedStrategy(null);
    const params = key === "strategy" ? "" : `?tab=${key}`;
    router.replace(params || "/", { scroll: false });
  }

  return (
    <div className="builder-dashboard">
      {/* 1-2-3 workflow step buttons */}
      <WorkflowSteps steps={steps} activeKey={activeSection} onSelect={switchTab} />

      {/* Content panels */}
      <div style={{ marginTop: 8 }}>
        {/* TAB 1: Strategy Builder */}
        {activeSection === "strategy" && (
          <Space direction="vertical" size="middle" style={{ width: "100%" }}>
            <DashboardCard title="Strategies" actions={<Tag color="blue">All statuses</Tag>}>
              <LaneStrategyTable
                lane="builder"
                onSelect={(s) => {
                  setSelectedStrategy(s);
                }}
              />
            </DashboardCard>
            <DashboardCard title="Strategy Editor">
              <AiStrategyCopilot />
            </DashboardCard>
          </Space>
        )}

        {/* TAB 2: Backtest Center */}
        {activeSection === "backtest" && (
          <Row gutter={[16, 16]}>
            <Col xs={24} xl={10}>
              <DashboardCard
                title="Strategies"
                actions={<Tag color="purple">Validated onward</Tag>}
              >
                <LaneStrategyTable
                  lane="backtest"
                  onSelect={(s) => setSelectedStrategy(s)}
                />
              </DashboardCard>
              {selectedStrategy && (
                <DashboardCard
                  title={`Spec: ${selectedStrategy.strategy_id}`}
                  actions={<Tag color="purple">AI review before backtest</Tag>}
                  
                  style={{ marginTop: 12 }}
                >
                  <Paragraph type="secondary">
                    Review or edit the StrategySpec before running. AI can check
                    correctness, parameter validity, and adapter compatibility.
                  </Paragraph>
                  <StrategySpecEditor spec={selectedStrategy.latest_spec} />
                </DashboardCard>
              )}
            </Col>
            <Col xs={24} xl={14}>
              <Space direction="vertical" size="middle" style={{ width: "100%" }}>
                <DashboardCard
                  title="BacktestNode Replay"
                  actions={<Tag color="purple">Historical evidence-only</Tag>}
                >
                  <BacktestLaunchPanel strategy={selectedStrategy} />
                  <Text type="secondary" style={{ display: "block", marginTop: 8 }}>
                    {JobTerminal()}
                  </Text>
                </DashboardCard>
                <DashboardCard
                  title="Manual Promotion Review"
                  actions={<Tag color="blue">Human gate</Tag>}
                >
                  <PromotionRequestPanel strategy={selectedStrategy} />
                </DashboardCard>
              </Space>
            </Col>
          </Row>
        )}

        {/* TAB 3: Execution Lane */}
        {activeSection === "execution" && (
          <Space direction="vertical" size="middle" style={{ width: "100%" }}>
            <DashboardCard
              title="Approved Strategies"
              actions={<Tag color="gold">Execution Ready</Tag>}
            >
              <LaneStrategyTable
                lane="execution"
                onSelect={(s) => setSelectedStrategy(s)}
              />
            </DashboardCard>
            {selectedStrategy && (
              <DashboardCard
                title={`Execution: ${selectedStrategy.strategy_id}`}
                actions={<Tag color="red">Backend-owned credentials</Tag>}
              >
                <ExecutionLaneFeaturePanel strategy={selectedStrategy} />
              </DashboardCard>
            )}
            {!selectedStrategy && (
              <DashboardCard
                title="Paper / Live TradingNode"
                actions={<Tag color="red">Backend-owned credentials</Tag>}
              >
                <Paragraph type="secondary">
                  Select an approved or execution-ready strategy above to
                  configure execution lane.
                </Paragraph>
                <ExecutionLaneFeaturePanel strategy={selectedStrategy} />
              </DashboardCard>
            )}
          </Space>
        )}
      </div>
    </div>
  );
}
