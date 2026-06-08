"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import {
  Button,
  Input,
  Select,
  Space,
  Table,
  Tag,
  Typography,
  Spin,
} from "antd";
import {
  BarChartOutlined,
  SearchOutlined,
} from "@ant-design/icons";
import { fetchResultList } from "../../lib/api";
import type { ResultListItem } from "../../lib/types";
import { ErrorStateCard } from "../ui/ErrorStateCard";
import { EmptyStateCard } from "../ui/EmptyStateCard";

const { Text } = Typography;

export function ResultsListClient() {
  const [results, setResults] = useState<ResultListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [search, setSearch] = useState("");
  const [sortBy, setSortBy] = useState<string>("date");

  useEffect(() => {
    fetchResultList()
      .then((data) => setResults(data))
      .catch((err) =>
        setError(
          err instanceof Error ? err.message : "Failed to load results",
        ),
      )
      .finally(() => setLoading(false));
  }, []);

  const filtered = useMemo(() => {
    const lowerSearch = search.trim().toLowerCase();
    const out = results.filter((r) => {
      if (!lowerSearch) return true;
      const id = r.result_id.toLowerCase();
      const lineage = (r.strategy_lineage_id ?? "").toLowerCase();
      return id.includes(lowerSearch) || lineage.includes(lowerSearch);
    });

    out.sort((a, b) => {
      switch (sortBy) {
        case "id":
          return a.result_id.localeCompare(b.result_id);
        case "strategy":
          return (a.strategy_lineage_id ?? "").localeCompare(
            b.strategy_lineage_id ?? "",
          );
        default:
          // date — newest first
          return (
            new Date(b.created_at).getTime() -
            new Date(a.created_at).getTime()
          );
      }
    });
    return out;
  }, [results, search, sortBy]);

  if (loading) return <Spin tip="Loading results..." />;
  if (error) {
    return (
      <ErrorStateCard
        message={error}
        detail="Check that the Builder backend is reachable."
        retryLabel="Retry"
        onRetry={() => window.location.reload()}
      />
    );
  }
  if (results.length === 0) {
    return (
      <EmptyStateCard
        title="Results"
        message="No backtest results yet."
        detail="Run a replay to generate observational evidence."
        actionLabel="Open Backtest Center"
        actionHref="/?tab=backtest"
      />
    );
  }

  return (
    <Space direction="vertical" style={{ width: "100%" }} size="middle">
      {/* Filter toolbar */}
      <Space wrap>
        <Input
          allowClear
          prefix={<SearchOutlined />}
          placeholder="Search by result or lineage ID"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{ width: 260 }}
        />
        <Select
          value={sortBy}
          onChange={(v) => setSortBy(v)}
          options={[
            { label: "Newest first", value: "date" },
            { label: "Result ID", value: "id" },
            { label: "Strategy", value: "strategy" },
          ]}
          style={{ width: 160 }}
        />
        <Text type="secondary" style={{ fontSize: 12 }}>
          {filtered.length} of {results.length} results
        </Text>
      </Space>

      <Table
        dataSource={filtered}
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
            render: (id: string) => (
              <a
                onClick={() => {
                  /* Could navigate to strategy detail if lineage mapped to strategy_id */
                }}
              >
                <Text>{id}</Text>
              </a>
            ),
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
              if (!m || Object.keys(m).length === 0)
                return <Text type="secondary">—</Text>;
              return (
                <Space size="small">
                  {Object.entries(m)
                    .slice(0, 3)
                    .map(([key, value]) => (
                      <Tag key={key} color="blue">
                        {key}:{" "}
                        {String(
                          typeof value === "number"
                            ? value.toFixed(4)
                            : value,
                        )}
                      </Tag>
                    ))}
                </Space>
              );
            },
          },
          {
            title: "Created",
            dataIndex: "created_at",
            render: (v: string) => (
              <Text type="secondary" style={{ fontSize: 12 }}>
                {v ? new Date(v).toLocaleDateString() : "—"}
              </Text>
            ),
          },
          {
            title: "",
            key: "actions",
            width: 80,
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
