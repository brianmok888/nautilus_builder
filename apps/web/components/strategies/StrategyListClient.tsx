"use client";

import { useRouter } from "next/navigation";

import { useCallback, useEffect, useState } from "react";
import { Button, Empty, Space, Table, Tag, Tooltip, Typography } from "antd";
import {
  CopyOutlined,
  EditOutlined,
  ExperimentOutlined,
} from "@ant-design/icons";
import { cloneStrategy, fetchStrategies } from "../../lib/api";
import type { StrategyStatus, StrategySummary } from "../../lib/types";
import { STRATEGY_STATUS_COLORS } from "../../lib/types";

const { Text } = Typography;

export function StrategyListClient() {
  const [strategies, setStrategies] = useState<StrategySummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const router = useRouter();

  const loadStrategies = useCallback(() => {
    setLoading(true);
    setError(null);
    fetchStrategies()
      .then((list) => {
        setStrategies(list);
        setLoading(false);
      })
      .catch(() => {
        setError("Unable to load strategies.");
        setLoading(false);
      });
  }, []);

  useEffect(() => {
    loadStrategies();
  }, [loadStrategies]);

  async function handleClone(strategyId: string) {
    setActionLoading(`clone:${strategyId}`);
    try {
      await cloneStrategy(strategyId);
      loadStrategies();
    } catch {
      setError("Unable to clone strategy.");
    } finally {
      setActionLoading(null);
    }
  }

  function handleEdit(strategy: StrategySummary) {
    router.push(`/builder/${strategy.strategy_id}`);
  }

  function handleBacktest(strategy: StrategySummary) {
    router.push(`/?tab=backtest`);
  }

  function canEdit(status: StrategyStatus): boolean {
    return status === "draft" || status === "validated";
  }

  function canBacktest(status: StrategyStatus): boolean {
    return ["draft", "validated", "backtested"].includes(status);
  }

  if (error) {
    return (
      <div style={{ padding: 12 }}>
        <Text type="secondary">{error}</Text>
      </div>
    );
  }

  if (!loading && strategies.length === 0) {
    return (
      <Empty
        description="No strategies yet. Use Strategy Builder to create one."
        image={Empty.PRESENTED_IMAGE_SIMPLE}
      />
    );
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
              <Tooltip title={canEdit(record.status) ? "Open in Builder" : `Edit not allowed for ${record.status}`}>
                <Button
                  size="small"
                  type="link"
                  icon={<EditOutlined />}
                  disabled={!canEdit(record.status)}
                  onClick={() => handleEdit(record)}
                >
                  Edit
                </Button>
              </Tooltip>
              <Tooltip title="Clone as new draft">
                <Button
                  size="small"
                  type="link"
                  icon={<CopyOutlined />}
                  loading={actionLoading === `clone:${record.strategy_id}`}
                  onClick={() => handleClone(record.strategy_id)}
                >
                  Clone
                </Button>
              </Tooltip>
              <Tooltip title={canBacktest(record.status) ? "Open in Backtest Center" : `Backtest not needed for ${record.status}`}>
                <Button
                  size="small"
                  type="link"
                  icon={<ExperimentOutlined />}
                  disabled={!canBacktest(record.status)}
                  onClick={() => handleBacktest(record)}
                >
                  Backtest
                </Button>
              </Tooltip>
            </Space>
          ),
        },
      ]}
    />
  );
}
