"use client";

import { useRouter } from "next/navigation";

import { useEffect, useState } from "react";
import {
  Button,
  Card,
  Descriptions,
  Empty,
  Space,
  Spin,
  Table,
  Tag,
  Typography,
} from "antd";
import {
  CopyOutlined,
  EditOutlined,
  ExperimentOutlined,
} from "@ant-design/icons";
import { cloneStrategy, fetchStrategyDetail } from "../../lib/api";
import type { StrategyStatus } from "../../lib/types";
import { STRATEGY_STATUS_COLORS } from "../../lib/types";

const { Text, Paragraph, Title } = Typography;

/** Lifecycle chain for visual status timeline */
const LIFECYCLE_CHAIN: StrategyStatus[] = [
  "draft",
  "validated",
  "backtested",
  "approved",
  "execution_ready",
];

export function StrategyDetailClient({ strategyId }: { strategyId: string }) {
  const [detail, setDetail] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [cloning, setCloning] = useState(false);

  const router = useRouter();

  useEffect(() => {
    fetchStrategyDetail(strategyId)
      .then((d) => setDetail(d as unknown as Record<string, unknown>))
      .catch(() => setError("Unable to load strategy detail."));
  }, [strategyId]);

  if (error) {
    return (
      <Card size="small">
        <Text type="danger">{error}</Text>
      </Card>
    );
  }

  if (!detail) {
    return (
      <div style={{ textAlign: "center", padding: 40 }}>
        <Spin size="large" />
      </div>
    );
  }

  const status = (detail.status as StrategyStatus) || "draft";
  const versions = (detail.versions as Array<{ strategy_version_id: string; spec: Record<string, unknown> }>) || [];
  const latestSpec = versions.length > 0 ? versions[versions.length - 1].spec : {};

  const indicators = (latestSpec.indicators as Record<string, { type: string; input: string; period: number }>) || {};
  const rules = (latestSpec.rules as Record<string, Record<string, unknown>>) || {};
  const risk = (latestSpec.risk as Record<string, number>) || {};
  const validation = (latestSpec.validation as Record<string, unknown>) || {};
  const dataRange = (latestSpec.data_range as { start: string; end: string }) || {};
  const provenance = (latestSpec.provenance as { created_by: string; parent_version_id?: string }) || {};

  function canEdit(): boolean {
    return status === "draft" || status === "validated";
  }

  function canBacktest(): boolean {
    return ["draft", "validated", "backtested"].includes(status);
  }

  async function handleClone() {
    setCloning(true);
    try {
      await cloneStrategy(strategyId);
      router.push("/strategies");
    } catch {
      setError("Clone failed.");
    } finally {
      setCloning(false);
    }
  }

  // Status timeline
  const currentIdx = LIFECYCLE_CHAIN.indexOf(status);

  return (
    <Space orientation="vertical" size="middle" style={{ width: "100%" }}>
      {/* Status timeline */}
      <Card size="small" title="Status">
        <Space wrap>
          {LIFECYCLE_CHAIN.map((s, idx) => {
            const reached = idx <= currentIdx;
            const current = s === status;
            return (
              <Tag
                key={s}
                color={current ? STRATEGY_STATUS_COLORS[s] : reached ? "blue" : "default"}
                style={{ opacity: reached ? 1 : 0.4 }}
              >
                {current ? "● " : reached ? "✓ " : "○ "}
                {s.replace("_", " ")}
              </Tag>
            );
          })}
        </Space>
      </Card>

      {/* Strategy overview */}
      <Card size="small" title="Overview">
        <Descriptions column={{ xs: 1, sm: 2, md: 3 }} size="small" bordered>
          <Descriptions.Item label="Strategy ID">
            <Text code>{strategyId}</Text>
          </Descriptions.Item>
          <Descriptions.Item label="Lineage">
            {String(detail.strategy_lineage_id ?? "")}
          </Descriptions.Item>
          <Descriptions.Item label="Status">
            <Tag color={STRATEGY_STATUS_COLORS[status]}>{status.replace("_", " ")}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="Adapter">
            {String(latestSpec.adapter_id ?? "")}
          </Descriptions.Item>
          <Descriptions.Item label="Venue">
            {String(latestSpec.venue ?? "")}
          </Descriptions.Item>
          <Descriptions.Item label="Instrument">
            {String(latestSpec.instrument_id ?? "")}
          </Descriptions.Item>
          <Descriptions.Item label="Bar Type">
            {String(latestSpec.bar_type ?? "")}
          </Descriptions.Item>
          <Descriptions.Item label="Data Range">
            {dataRange.start && dataRange.end
              ? `${dataRange.start} → ${dataRange.end}`
              : "—"}
          </Descriptions.Item>
          <Descriptions.Item label="Created By">
            {String(provenance.created_by ?? "—")}
          </Descriptions.Item>
        </Descriptions>
      </Card>

      {/* Indicators */}
      <Card size="small" title="Indicators">
        <Table
          size="small"
          pagination={false}
          dataSource={Object.entries(indicators).map(([name, spec]) => ({
            key: name,
            name,
            type: spec.type,
            input: spec.input,
            period: spec.period,
          }))}
          columns={[
            { title: "Name", dataIndex: "name", key: "name" },
            { title: "Type", dataIndex: "type", key: "type" },
            { title: "Input", dataIndex: "input", key: "input" },
            { title: "Period", dataIndex: "period", key: "period" },
          ]}
        />
      </Card>

      {/* Rules */}
      <Card size="small" title="Entry/Exit Rules">
        <Space orientation="vertical" style={{ width: "100%" }}>
          {Object.entries(rules).map(([name, block]) => (
            <Descriptions
              key={name}
              title={name.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}
              size="small"
              bordered
              column={1}
            >
              <Descriptions.Item label="Logic">
                {"all" in block && block.all ? "ALL (and)" : "ANY (or)"}
              </Descriptions.Item>
              <Descriptions.Item label="Clauses">
                <Space wrap>
                  {((block.all || block.any) as Array<Record<string, unknown>>)?.map((clause, idx) => {
                    const operator = Object.entries(clause).find(([, v]) => v !== null);
                    if (!operator) return <Tag key={idx}>—</Tag>;
                    return (
                      <Tag key={idx} color="blue">
                        {operator[0]}({Array.isArray(operator[1]) ? (operator[1] as unknown[]).join(", ") : String(operator[1])})
                      </Tag>
                    );
                  })}
                </Space>
              </Descriptions.Item>
            </Descriptions>
          ))}
        </Space>
      </Card>

      {/* Risk */}
      <Card size="small" title="Risk Parameters">
        <Descriptions column={{ xs: 1, sm: 2 }} size="small" bordered>
          <Descriptions.Item label="Position Size %">
            {((risk.position_size_pct ?? 0) * 100).toFixed(1)}%
          </Descriptions.Item>
          <Descriptions.Item label="Stop Loss %">
            {((risk.stop_loss_pct ?? 0) * 100).toFixed(1)}%
          </Descriptions.Item>
          <Descriptions.Item label="Take Profit %">
            {((risk.take_profit_pct ?? 0) * 100).toFixed(1)}%
          </Descriptions.Item>
          <Descriptions.Item label="Max Hold Bars">
            {String(risk.max_hold_bars ?? "—")}
          </Descriptions.Item>
        </Descriptions>
      </Card>

      {/* Validation flags */}
      <Card size="small" title="Validation">
        <Space wrap>
          {Object.entries(validation).map(([key, value]) => (
            <Tag key={key} color={value === true ? "green" : value === false ? "red" : "default"}>
              {key.replace(/_/g, " ")}: {String(value)}
            </Tag>
          ))}
        </Space>
      </Card>

      {/* Version history */}
      <Card size="small" title="Version History" extra={<Tag>{versions.length} version{versions.length !== 1 ? "s" : ""}</Tag>}>
        <Table
          size="small"
          pagination={false}
          dataSource={versions.map((v, idx) => ({ key: v.strategy_version_id, ...v, idx: idx + 1 }))}
          columns={[
            { title: "#", dataIndex: "idx", width: 40 },
            { title: "Version ID", dataIndex: "strategy_version_id", render: (id: string) => <Text code>{id}</Text> },
            {
              title: "Stage",
              key: "stage",
              render: (_, record) => {
                const s = (record.spec as Record<string, unknown>)?.stage;
                return s ? <Tag>{String(s)}</Tag> : "—";
              },
            },
          ]}
        />
      </Card>

      {/* Actions */}
      <Card size="small" title="Actions">
        <Space>
          <Button
            icon={<EditOutlined />}
            disabled={!canEdit()}
            onClick={() => router.push(`/builder/${strategyId}`)}
          >
            Edit in Builder
          </Button>
          <Button
            icon={<CopyOutlined />}
            loading={cloning}
            onClick={handleClone}
          >
            Clone as Draft
          </Button>
          <Button
            icon={<ExperimentOutlined />}
            disabled={!canBacktest()}
            onClick={() => router.push(`/?tab=backtest`)}
          >
            Backtest
          </Button>
        </Space>
      </Card>
    </Space>
  );
}
