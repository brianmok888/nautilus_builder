"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Table, Tag, Typography, Empty, Spin, Card, Space } from "antd";
import { BarChartOutlined } from "@ant-design/icons";
import { fetchResultList } from "../../lib/api";
import type { ResultListItem } from "../../lib/types";

const { Title, Text } = Typography;

export function ResultsListClient() {
  const [results, setResults] = useState<ResultListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchResultList()
      .then((data) => setResults(data))
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load results"))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <Spin tip="Loading results..." />;
  if (error) return <Card><Text type="danger">{error}</Text></Card>;
  if (results.length === 0) {
    return (
      <Empty description="No backtest results yet">
        <Link href="/?tab=backtest">Run a backtest to see results</Link>
      </Empty>
    );
  }

  return (
    <Space direction="vertical" style={{ width: "100%" }} size="middle">
      <Card>
        <Title level={4}>Backtest Results</Title>
        <Text type="secondary">
          Observational results and reports from backtest runs. No execution authority.
        </Text>
      </Card>
      <Table
        dataSource={results}
        rowKey="result_id"
        pagination={{ pageSize: 20 }}
        columns={[
          {
            title: "Result ID",
            dataIndex: "result_id",
            render: (id: string) => (
              <Link href={`/results/${id}`}>
                <Text code>{id}</Text>
              </Link>
            ),
          },
          {
            title: "Strategy",
            dataIndex: "strategy_lineage_id",
            render: (id: string) => <Text>{id}</Text>,
          },
          {
            title: "Version",
            dataIndex: "strategy_version_id",
            render: (id: string) => <Tag>{id}</Tag>,
          },
          {
            title: "Key Metrics",
            key: "metrics",
            render: (_, record) => {
              const m = record.metrics;
              if (!m || Object.keys(m).length === 0) return <Text type="secondary">—</Text>;
              return (
                <Space size="small">
                  {Object.entries(m)
                    .slice(0, 3)
                    .map(([key, value]) => (
                      <Tag key={key} color="blue">
                        {key}: {String(typeof value === "number" ? value.toFixed(4) : value)}
                      </Tag>
                    ))}
                </Space>
              );
            },
          },
          {
            title: "",
            key: "actions",
            render: (_, record) => (
              <Link href={`/results/${record.result_id}`}>
                <BarChartOutlined /> View
              </Link>
            ),
          },
        ]}
      />
    </Space>
  );
}
