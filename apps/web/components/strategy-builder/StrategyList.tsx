"use client";

import { useEffect, useState } from "react";
import { Button, Card, Empty, Space, Table, Tag, Typography } from "antd";
import { fetchStrategies } from "../../lib/api";
import type { StrategySummary } from "../../lib/types";

const { Text } = Typography;

export const StrategyList = ({
  onSelect,
  onClone,
}: {
  onSelect?: (strategyId: string) => void;
  onClone?: (strategyId: string) => void;
}) => {
  const [strategies, setStrategies] = useState<StrategySummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchStrategies()
      .then((list) => {
        setStrategies(list);
        setLoading(false);
      })
      .catch((err: Error) => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  if (error) {
    return (
      <Card size="small">
        <Text type="secondary">Unable to load strategies: {error}</Text>
      </Card>
    );
  }

  if (!loading && strategies.length === 0) {
    return (
      <Card size="small">
        <Empty
          description="No strategies yet. Use the AI prompt above to create one."
          image={Empty.PRESENTED_IMAGE_SIMPLE}
        />
      </Card>
    );
  }

  return (
    <Card size="small" title="Strategies" extra={<Tag>{strategies.length}</Tag>}>
      <Table
        size="small"
        loading={loading}
        dataSource={strategies}
        rowKey="strategy_id"
        pagination={{ pageSize: 10, size: "small" }}
        columns={[
          {
            title: "ID",
            dataIndex: "strategy_id",
            key: "id",
            ellipsis: true,
            width: "35%",
            render: (id: string) => <Text code>{id}</Text>,
          },
          {
            title: "Lineage",
            dataIndex: "strategy_lineage_id",
            key: "lineage",
            ellipsis: true,
            width: "35%",
          },
          {
            title: "Actions",
            key: "actions",
            width: "30%",
            render: (_, record) => (
              <Space size="small">
                <Button
                  size="small"
                  type="link"
                  onClick={() => onSelect?.(record.strategy_id)}
                >
                  Edit
                </Button>
                <Button
                  size="small"
                  type="link"
                  onClick={() => onClone?.(record.strategy_id)}
                >
                  Clone
                </Button>
              </Space>
            ),
          },
        ]}
      />
    </Card>
  );
};
