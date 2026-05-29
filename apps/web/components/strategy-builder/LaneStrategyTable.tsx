"use client";

import { useCallback, useEffect, useState } from "react";
import { Button, Empty, Space, Table, Tag, Tooltip, Typography } from "antd";
import {
  CopyOutlined,
  EditOutlined,
  ExperimentOutlined,
  SafetyCertificateOutlined,
  ThunderboltOutlined,
} from "@ant-design/icons";
import { approveStrategy, cloneStrategy, fetchStrategies } from "../../lib/api";
import type { StrategyStatus, StrategySummary } from "../../lib/types";
import { LANE_ALLOWED_STATUSES, STRATEGY_STATUS_COLORS } from "../../lib/types";

const { Text } = Typography;

export type LaneKey = "builder" | "backtest" | "execution";

type LaneAction = {
  key: string;
  label: string;
  icon: React.ReactNode;
  allowedStatuses: StrategyStatus[];
  tooltip: string;
};

const ALL_STATUSES: StrategyStatus[] = [
  "draft", "validated", "backtested", "approved", "execution_ready",
];

const LANE_ACTIONS: Record<LaneKey, LaneAction[]> = {
  builder: [
    { key: "edit", label: "Edit", icon: <EditOutlined />, allowedStatuses: ["draft", "validated"], tooltip: "Edit strategy spec" },
    { key: "clone", label: "Clone", icon: <CopyOutlined />, allowedStatuses: ALL_STATUSES, tooltip: "Clone as new draft" },
  ],
  backtest: [
    { key: "select", label: "Select", icon: <ExperimentOutlined />, allowedStatuses: ["validated", "backtested", "approved", "execution_ready"], tooltip: "Load into backtest panel" },
    { key: "approve", label: "Approve", icon: <SafetyCertificateOutlined />, allowedStatuses: ["backtested"], tooltip: "Approve after backtest review" },
    { key: "clone", label: "Clone", icon: <CopyOutlined />, allowedStatuses: ALL_STATUSES, tooltip: "Clone as new draft" },
  ],
  execution: [
    { key: "load", label: "Load", icon: <ThunderboltOutlined />, allowedStatuses: ["approved", "execution_ready"], tooltip: "Load into execution lane" },
    { key: "promote", label: "→ Execution Ready", icon: <SafetyCertificateOutlined />, allowedStatuses: ["approved"], tooltip: "Promote to execution ready after paper/shadow verification" },
  ],
};

export function LaneStrategyTable({
  lane,
  onSelect,
  onActionComplete,
}: {
  lane: LaneKey;
  onSelect?: (strategy: StrategySummary) => void;
  onActionComplete?: () => void;
}) {
  const [strategies, setStrategies] = useState<StrategySummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const allowedStatuses = LANE_ALLOWED_STATUSES[lane];
  const actions = LANE_ACTIONS[lane];

  const loadStrategies = useCallback(() => {
    setLoading(true);
    setError(null);
    fetchStrategies()
      .then((all) => {
        const filtered = all.filter((s) => allowedStatuses.includes(s.status));
        setStrategies(filtered);
        setLoading(false);
      })
      .catch((err: Error) => {
        setError(err.message);
        setLoading(false);
      });
  }, [allowedStatuses]);

  useEffect(() => {
    loadStrategies();
  }, [loadStrategies]);

  async function handleAction(actionKey: string, strategy: StrategySummary) {
    setActionLoading(`${actionKey}:${strategy.strategy_id}`);
    try {
      switch (actionKey) {
        case "clone":
          await cloneStrategy(strategy.strategy_id);
          break;
        case "approve":
        case "promote":
          await approveStrategy(strategy.strategy_id);
          break;
        case "edit":
        case "select":
        case "load":
          onSelect?.(strategy);
          break;
      }
      if (actionKey === "clone" || actionKey === "approve" || actionKey === "promote") {
        loadStrategies();
        onActionComplete?.();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setActionLoading(null);
    }
  }

  if (error) {
    return (
      <div style={{ padding: 12 }}>
        <Text type="secondary">Unable to load strategies: {error}</Text>
      </div>
    );
  }

  if (!loading && strategies.length === 0) {
    const emptyMessages: Record<LaneKey, string> = {
      builder: "No strategies yet. Use AI prompt to create one.",
      backtest: "No strategies available for backtest. Validate a draft in Strategy Builder first.",
      execution: "No approved strategies. Strategies must pass backtest and human approval first.",
    };
    return <Empty description={emptyMessages[lane]} image={Empty.PRESENTED_IMAGE_SIMPLE} />;
  }

  return (
    <Table
      size="small"
      loading={loading}
      dataSource={strategies}
      rowKey="strategy_id"
      pagination={{ pageSize: 10, size: "small" }}
      columns={[
        {
          title: "Strategy ID",
          dataIndex: "strategy_id",
          key: "id",
          ellipsis: true,
          width: "28%",
          render: (id: string) => <Text code>{id}</Text>,
        },
        {
          title: "Lineage",
          dataIndex: "strategy_lineage_id",
          key: "lineage",
          ellipsis: true,
          width: "22%",
        },
        {
          title: "Status",
          dataIndex: "status",
          key: "status",
          width: "16%",
          render: (status: StrategyStatus) => (
            <Tag color={STRATEGY_STATUS_COLORS[status]}>{status.replace("_", " ")}</Tag>
          ),
        },
        {
          title: "Actions",
          key: "actions",
          width: "34%",
          render: (_, record) => (
            <Space size="small">
              {actions.map((action) => {
                const allowed = action.allowedStatuses.includes(record.status);
                const isLoading = actionLoading === `${action.key}:${record.strategy_id}`;
                return (
                  <Tooltip key={action.key} title={allowed ? action.tooltip : `Not available for ${record.status.replace("_", " ")} strategies`}>
                    <Button
                      size="small"
                      type={action.key === "approve" || action.key === "promote" ? "primary" : "link"}
                      icon={action.icon}
                      loading={isLoading}
                      disabled={!allowed || isLoading}
                      onClick={() => handleAction(action.key, record)}
                    >
                      {action.label}
                    </Button>
                  </Tooltip>
                );
              })}
            </Space>
          ),
        },
      ]}
    />
  );
}
