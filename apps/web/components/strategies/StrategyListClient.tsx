"use client";

import { useRouter } from "next/navigation";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Button,
  Input,
  Select,
  Space,
  Table,
  Tag,
  Tooltip,
  Typography,
} from "antd";
import {
  CopyOutlined,
  EditOutlined,
  ExperimentOutlined,
  SearchOutlined,
} from "@ant-design/icons";
import { cloneStrategy, fetchStrategies } from "../../lib/api";
import type { StrategyStatus, StrategySummary } from "../../lib/types";
import { STRATEGY_STATUS_COLORS } from "../../lib/types";
import { ErrorStateCard } from "../ui/ErrorStateCard";
import { EmptyStateCard } from "../ui/EmptyStateCard";

const { Text } = Typography;

const STATUS_FILTER_OPTIONS: { label: string; value: StrategyStatus | "all" }[] =
  [
    { label: "All statuses", value: "all" },
    { label: "Draft", value: "draft" },
    { label: "Validated", value: "validated" },
    { label: "Backtested", value: "backtested" },
    { label: "Approved", value: "approved" },
    { label: "Execution ready", value: "execution_ready" },
  ];

const SORT_OPTIONS: { label: string; value: string }[] = [
  { label: "Status", value: "status" },
  { label: "Strategy ID", value: "id" },
  { label: "Lineage", value: "lineage" },
];

export function StrategyListClient() {
  const [strategies, setStrategies] = useState<StrategySummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  // Filters
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<StrategyStatus | "all">(
    "all",
  );
  const [sortBy, setSortBy] = useState<string>("status");

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

  // Derived filtered + sorted data
  const filtered = useMemo(() => {
    const lowerSearch = search.trim().toLowerCase();
    const out = strategies.filter((s) => {
      if (statusFilter !== "all" && s.status !== statusFilter) return false;
      if (!lowerSearch) return true;
      const id = s.strategy_id.toLowerCase();
      const lineage = (s.strategy_lineage_id ?? "").toLowerCase();
      return id.includes(lowerSearch) || lineage.includes(lowerSearch);
    });

    out.sort((a, b) => {
      switch (sortBy) {
        case "id":
          return a.strategy_id.localeCompare(b.strategy_id);
        case "lineage":
          return (a.strategy_lineage_id ?? "").localeCompare(
            b.strategy_lineage_id ?? "",
          );
        default:
          // status — preserve enum ordering
          const order: StrategyStatus[] = [
            "draft",
            "validated",
            "backtested",
            "approved",
            "execution_ready",
          ];
          return order.indexOf(a.status) - order.indexOf(b.status);
      }
    });
    return out;
  }, [strategies, search, statusFilter, sortBy]);

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

  function handleBacktest() {
    router.push("/backtests");
  }

  function canEdit(status: StrategyStatus): boolean {
    return status === "draft" || status === "validated";
  }

  function canBacktest(status: StrategyStatus): boolean {
    return ["draft", "validated", "backtested"].includes(status);
  }

  if (error) {
    return (
      <ErrorStateCard
        message={error}
        detail="Check that the Builder backend is reachable."
        retryLabel="Retry"
        onRetry={loadStrategies}
      />
    );
  }

  if (!loading && strategies.length === 0) {
    return (
      <EmptyStateCard
        title="Strategy Specs"
        message="No strategy specs yet."
        detail="Create your first Builder draft to get started."
        actionLabel="Open Strategy Builder"
        actionHref="/builder"
      />
    );
  }

  return (
    <Space direction="vertical" size="middle" style={{ width: "100%" }}>
      {/* Filter toolbar */}
      <Space wrap>
        <Input
          allowClear
          prefix={<SearchOutlined />}
          placeholder="Search by ID or lineage"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{ width: 260 }}
        />
        <Select
          value={statusFilter}
          onChange={(v) => setStatusFilter(v)}
          options={STATUS_FILTER_OPTIONS}
          style={{ width: 160 }}
        />
        <Select
          value={sortBy}
          onChange={(v) => setSortBy(v)}
          options={SORT_OPTIONS}
          style={{ width: 140 }}
        />
        <Text type="secondary" style={{ fontSize: 12 }}>
          {filtered.length} of {strategies.length} strategies
        </Text>
      </Space>

      <Table
        size="small"
        loading={loading}
        dataSource={filtered}
        rowKey="strategy_id"
        pagination={{ pageSize: 10, size: "small" }}
        columns={[
          {
            title: "Strategy ID",
            dataIndex: "strategy_id",
            key: "id",
            ellipsis: true,
            width: "26%",
            render: (id: string) => (
              <a
                onClick={() => router.push(`/strategies/${id}`)}
                style={{ cursor: "pointer" }}
              >
                <Text code>{id}</Text>
              </a>
            ),
          },
          {
            title: "Lineage",
            dataIndex: "strategy_lineage_id",
            key: "lineage",
            ellipsis: true,
            width: "22%",
            render: (v: string) => <Text type="secondary">{v}</Text>,
          },
          {
            title: "Status",
            dataIndex: "status",
            key: "status",
            width: "16%",
            render: (status: StrategyStatus) => (
              <Tag color={STRATEGY_STATUS_COLORS[status]}>
                {status.replace("_", " ")}
              </Tag>
            ),
          },
          {
            title: "Actions",
            key: "actions",
            width: "36%",
            render: (_, record) => (
              <Space size="small">
                <Tooltip
                  title={
                    canEdit(record.status)
                      ? "Open in Builder"
                      : `Edit not allowed for ${record.status}`
                  }
                >
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
                <Tooltip
                  title={
                    canBacktest(record.status)
                      ? "Open in Backtest Center"
                      : `Backtest not needed for ${record.status}`
                  }
                >
                  <Button
                    size="small"
                    type="link"
                    icon={<ExperimentOutlined />}
                    disabled={!canBacktest(record.status)}
                    onClick={handleBacktest}
                  >
                    Backtest
                  </Button>
                </Tooltip>
              </Space>
            ),
          },
        ]}
      />
    </Space>
  );
}
