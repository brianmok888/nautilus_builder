"use client";

import { useEffect, useState } from "react";
import {
  CodeOutlined,
  ExperimentOutlined,
  PlayCircleOutlined,
} from "@ant-design/icons";
import { useRouter } from "next/navigation";
import { Descriptions, Space, Tag, Typography } from "antd";
import { AiStrategyCopilot } from "../ai-builder/AiStrategyCopilot";
import { BacktestLaunchPanel } from "../backtests/BacktestLaunchPanel";
import { BuilderOverview } from "./BuilderOverview";
import { ExecutionLaneFeaturePanel } from "../config/ExecutionLaneFeaturePanel";
import { PromotionRequestPanel } from "../promotions/PromotionRequestPanel";
import { LaneStrategyTable } from "../strategy-builder/LaneStrategyTable";
import { StrategySpecEditor } from "../strategy-builder/StrategySpecEditor";
import { JobTerminal } from "../terminal/JobTerminal";
import { DashboardCard } from "../ui/DashboardCard";
import { WorkflowSteps, type WorkflowStep } from "../ui/WorkflowSteps";
import { BuilderSafetyStatusPanel } from "../safety/BuilderSafetyStatusPanel";
import type { StrategySummary } from "../../lib/types";

const { Text, Paragraph } = Typography;

const sectionPaths: Record<string, string> = {
  overview: "/",
  strategy: "/builder",
  backtest: "/backtests",
  execution: "/execution",
};

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

function textOrDash(value: unknown): string {
  if (value === undefined || value === null || value === "") return "—";
  return String(value);
}

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
    router.replace(sectionPaths[key] ?? "/", { scroll: false });
  }

  return (
    <div className="builder-dashboard">
      {/* 1-2-3 workflow step buttons */}
      <WorkflowSteps steps={steps} activeKey={activeSection} onSelect={switchTab} />

      {/* Builder safety status — always visible */}
      <div style={{ marginTop: 8 }}>
        <BuilderSafetyStatusPanel />
      </div>

      {/* Content panels */}
      <div style={{ marginTop: 8 }}>
        {activeSection === "overview" && <BuilderOverview />}

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

        {/* TAB 2: Backtest Center — top-down workflow */}
        {activeSection === "backtest" && (
          <div className="backtest-center-flow">
            {/* Step 1: Strategy Selection — full width */}
            <DashboardCard
              title="Strategies"
              subtitle="Select a validated StrategySpec before creating a BacktestNode replay manifest."
              actions={<Tag color="purple">Validated onward</Tag>}
            >
              <LaneStrategyTable
                lane="backtest"
                onSelect={(s) => setSelectedStrategy(s)}
              />
            </DashboardCard>

            {/* Step 2: Selected Validated Strategy summary */}
            {selectedStrategy && (
              <DashboardCard
                title="Selected Validated Strategy"
                subtitle="Evidence summary for the strategy that will be used in the replay manifest."
                actions={<Tag color="purple">Strategy evidence</Tag>}
              >
                <Descriptions
                  column={{ xs: 1, sm: 2, lg: 3 }}
                  size="small"
                  bordered
                >
                  <Descriptions.Item label="Strategy">
                    <Text code>{selectedStrategy.strategy_id}</Text>
                  </Descriptions.Item>
                  <Descriptions.Item label="Lineage">
                    {textOrDash(selectedStrategy.strategy_lineage_id)}
                  </Descriptions.Item>
                  <Descriptions.Item label="Version">
                    {textOrDash(selectedStrategy.strategy_id + '_v001')}
                  </Descriptions.Item>
                  <Descriptions.Item label="Status">
                    <Tag color="purple">{selectedStrategy.status.replace(/_/g, " ")}</Tag>
                  </Descriptions.Item>
                  <Descriptions.Item label="Adapter">
                    {textOrDash((selectedStrategy.latest_spec as Record<string, unknown>)?.adapter_id)}
                  </Descriptions.Item>
                  <Descriptions.Item label="Instrument">
                    {textOrDash((selectedStrategy.latest_spec as Record<string, unknown>)?.instrument_id)}
                  </Descriptions.Item>
                  <Descriptions.Item label="Data range">
                    {textOrDash(
                      typeof (selectedStrategy.latest_spec as Record<string, unknown>)?.data_range === "object"
                        ? JSON.stringify((selectedStrategy.latest_spec as Record<string, unknown>)?.data_range)
                        : (selectedStrategy.latest_spec as Record<string, unknown>)?.data_range,
                    )}
                  </Descriptions.Item>
                  <Descriptions.Item label="Data type">
                    {textOrDash((selectedStrategy.latest_spec as Record<string, unknown>)?.data_type)}
                  </Descriptions.Item>
                  <Descriptions.Item label="Timeframe">
                    {textOrDash(
                      (selectedStrategy.latest_spec as Record<string, unknown>)?.bar_type
                        ? String(((selectedStrategy.latest_spec as Record<string, unknown>)?.bar_type as string) || "").split("-").slice(-2, -1)[0] || "—"
                        : "—",
                    )}
                  </Descriptions.Item>
                </Descriptions>

                {/* Spec preview */}
                <div style={{ marginTop: 12 }}>
                  <StrategySpecEditor spec={selectedStrategy.latest_spec} />
                </div>
              </DashboardCard>
            )}

            {/* Step 3: BacktestNode Replay manifest — full width */}
            <DashboardCard
              title="BacktestNode Replay"
              subtitle="Run manifest for historical evidence-only backtest."
              actions={<Tag color="purple">Historical evidence-only</Tag>}
            >
              <BacktestLaunchPanel strategy={selectedStrategy} />
              <Text type="secondary" style={{ display: "block", marginTop: 8 }}>
                {JobTerminal()}
              </Text>
            </DashboardCard>

            {/* Step 4: Manual Promotion Review — full width */}
            <DashboardCard
              title="Manual Promotion Review"
              subtitle="Human gate for promotion readiness."
              actions={<Tag color="blue">Human gate</Tag>}
            >
              <PromotionRequestPanel strategy={selectedStrategy} />
            </DashboardCard>
          </div>
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
