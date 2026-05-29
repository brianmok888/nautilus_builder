"use client";

import { useCallback, useEffect, useState } from "react";
import { Button, Empty, Space, Table, Tag, Tooltip, Typography } from "antd";
import {
  CheckCircleOutlined,
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

const LANE_ACTIONS: Record<LaneKey, LaneAction[]> = {
  builder: [
    { key: "edit", label: "Edit", icon: <EditOutlined />, allowedStatuses: ["draft", "validated"], tooltip: "Edit strategy spec" },
    { key: "clone", label: "Clone", icon: <CopyOutlined />, allowedStatuses: ["draft", "validated", "backtested", "approved"], tooltip: "Clone as new draft" },
  ],
  backtest: [
    { key: "select", label: "Select", icon: <ExperimentOutlined />, allowedStatuses: ["draft", "validated", "approved"], tooltip: "Load into backtest panel" },
    { key: "approve", label: "Approve", icon: <SafetyCertificateOutlined />, allowedStatuses: ["backtested", "shadow_candidate"], tooltip: "Promote to execution-ready" },
    { key: "clone", label: "Clone", icon: <CopyOutlined />, allowedStatuses: ["draft", "validated", "backtested", "approved"], tooltip: "Clone as new draft" },
  ],
  execution: [
    { key: "load", label: "Load", icon: <ThunderboltOutlined />, allowedStatuses: ["approved", "execution_ready"], tooltip: "Load into execution lane" },
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
          await approveStrategy(strategy.strategy_id);
          break;
        case "edit":
        case "select":
        case "load":
          onSelect?.(strategy);
          break;
      }
      if (actionKey === "clone" || actionKey === "approve") {
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
      builder: "No draft or validated strategies. Use AI prompt to create one.",
      backtest: "No strategies available for backtest. Create and validate one in Strategy Builder first.",
      execution: "No approved or execution-ready strategies. Strategies must pass backtest review and approval first.",
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
                  <Tooltip key={action.key} title={allowed ? action.tooltip : `Not allowed for ${record.status} strategies`}>
                    <Button
                      size="small"
                      type={action.key === "approve" ? "primary" : "link"}
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
