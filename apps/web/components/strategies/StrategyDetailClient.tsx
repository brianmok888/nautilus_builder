"use client";

import { useRouter } from "next/navigation";

import { useEffect, useMemo, useState } from "react";
import {
  Alert,
  Button,
  Card,
  Descriptions,
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
import { cloneStrategy, fetchStrategyDetail, fetchStrategyEvidenceSummary } from "../../lib/api";
import type { StrategyStatus, StrategyEvidenceSummary } from "../../lib/types";
import { STRATEGY_STATUS_COLORS } from "../../lib/types";

import { StrategyLifecyclePanel } from "../lifecycle/StrategyLifecyclePanel";
import { NextActionCard } from "../lifecycle/NextActionCard";
import { EvidenceSummaryGrid } from "../evidence/EvidenceSummaryGrid";
import { AuditTimeline } from "../audit/AuditTimeline";
import { deriveStrategyLifecycle } from "../../lib/lifecycle/deriveStrategyLifecycle";
import { deriveEvidenceRefs } from "../../lib/lifecycle/deriveEvidenceRefs";
import { deriveAuditEvents } from "../../lib/lifecycle/deriveAuditEvents";
import {
  mapLifecycleInput,
  mapEvidenceInput,
  mapAuditInput,
} from "../../lib/lifecycle/mapEvidenceSummary";

const { Text, Paragraph } = Typography;

export function StrategyDetailClient({ strategyId }: { strategyId: string }) {
  const [detail, setDetail] = useState<Record<string, unknown> | null>(null);
  const [evidenceSummary, setEvidenceSummary] = useState<StrategyEvidenceSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [evidenceSummaryError, setEvidenceSummaryError] = useState<boolean>(false);
  const [cloning, setCloning] = useState(false);

  const router = useRouter();

  useEffect(() => {
    setEvidenceSummaryError(false);
    fetchStrategyDetail(strategyId)
      .then((d) => setDetail(d as unknown as Record<string, unknown>))
      .catch(() => setError("Unable to load strategy detail."));

    fetchStrategyEvidenceSummary(strategyId)
      .then((s) => setEvidenceSummary(s))
      .catch(() => {
        // Evidence summary is best-effort. If it fails, we fall back to
        // deriving from strategy detail alone.
        setEvidenceSummaryError(true);
      });
  }, [strategyId]);

  // ── Hooks must be above any early returns ──────────────────────
  const status = (detail?.status as StrategyStatus) || "draft";
  const versions =
    (detail?.versions as Array<{
      strategy_version_id: string;
      spec: Record<string, unknown>;
    }>) || [];
  const latestSpec = versions.length > 0 ? versions[versions.length - 1].spec : {};
  const validation = (latestSpec.validation as Record<string, unknown>) || {};
  const provenance =
    (latestSpec.provenance as {
      created_by: string;
      parent_version_id?: string;
    }) || {};

  // Derive lifecycle from evidence summary when available, otherwise from strategy detail.
  const lifecycleInput = useMemo(
    () =>
      evidenceSummary
        ? mapLifecycleInput(evidenceSummary)
        : {
            strategyId,
            strategyName: String(latestSpec.instrument_id ?? strategyId),
            status,
            validation,
          },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [evidenceSummary, status, strategyId, latestSpec.instrument_id, validation],
  );

  const lifecycleSummary = useMemo(
    () => deriveStrategyLifecycle(lifecycleInput),
    [lifecycleInput],
  );

  const evidenceInput = useMemo(
    () =>
      evidenceSummary
        ? mapEvidenceInput(evidenceSummary)
        : { strategyId, validation, status },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [evidenceSummary, status, strategyId, validation],
  );

  const evidenceRefs = useMemo(
    () => deriveEvidenceRefs(evidenceInput),
    [evidenceInput],
  );

  const auditInput = useMemo(
    () =>
      evidenceSummary
        ? mapAuditInput(evidenceSummary)
        : {
            strategyId,
            strategyLineageId: String(detail?.strategy_lineage_id ?? ""),
            status,
            createdBy: provenance.created_by,
            validation,
          },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [evidenceSummary, status, strategyId, validation, provenance.created_by, detail?.strategy_lineage_id],
  );

  const auditEvents = useMemo(
    () => deriveAuditEvents(auditInput),
    [auditInput],
  );

  // ── Early returns (after hooks) ────────────────────────────────
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

  // ── Derived data (non-hook) ────────────────────────────────────
  const indicators =
    (latestSpec.indicators as Record<
      string,
      { type: string; input: string; period: number }
    >) || {};
  const rules =
    (latestSpec.rules as Record<string, Record<string, unknown>>) || {};
  const risk = (latestSpec.risk as Record<string, number>) || {};
  const dataRange =
    (latestSpec.data_range as { start: string; end: string }) || {};

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

  return (
    <Space direction="vertical" size="middle" style={{ width: "100%" }}>
      {/* ── Lifecycle panel ─────────────────────────────────────── */}
      <StrategyLifecyclePanel summary={lifecycleSummary} />

      {/* ── Next action guidance ─────────────────────────────────── */}
      <NextActionCard
        action={lifecycleSummary.nextAction}
        blockingReasons={lifecycleSummary.blockingReasons}
        links={{
          validation: `/builder/${strategyId}`,
          replay: `/?tab=backtest`,
          promotion: `/?tab=backtest`,
        }}
        onRunReplay={() => router.push(`/?tab=backtest`)}
      />

      {/* ── Evidence dashboard ──────────────────────────────────── */}
      <EvidenceSummaryGrid evidenceRefs={evidenceRefs} />

      {/* ── Strategy overview ───────────────────────────────────── */}
      <Card size="small" title="Overview">
        <Descriptions
          column={{ xs: 1, sm: 2, md: 3 }}
          size="small"
          bordered
        >
          <Descriptions.Item label="Strategy ID">
            <Text code>{strategyId}</Text>
          </Descriptions.Item>
          <Descriptions.Item label="Lineage">
            {String(detail.strategy_lineage_id ?? "")}
          </Descriptions.Item>
          <Descriptions.Item label="Status">
            <Tag color={STRATEGY_STATUS_COLORS[status]}>
              {status.replace("_", " ")}
            </Tag>
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

      {/* ── Indicators ──────────────────────────────────────────── */}
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

      {/* ── Rules ───────────────────────────────────────────────── */}
      <Card size="small" title="Entry/Exit Rules">
        <Space direction="vertical" style={{ width: "100%" }}>
          {Object.entries(rules).map(([name, block]) => (
            <Descriptions
              key={name}
              title={name
                .replace(/_/g, " ")
                .replace(/\b\w/g, (c) => c.toUpperCase())}
              size="small"
              bordered
              column={1}
            >
              <Descriptions.Item label="Logic">
                {"all" in block && block.all ? "ALL (and)" : "ANY (or)"}
              </Descriptions.Item>
              <Descriptions.Item label="Clauses">
                <Space wrap>
                  {(
                    (block.all || block.any) as Array<Record<string, unknown>>
                  )?.map((clause, idx) => {
                    const operator = Object.entries(clause).find(
                      ([, v]) => v !== null,
                    );
                    if (!operator) return <Tag key={idx}>—</Tag>;
                    return (
                      <Tag key={idx} color="blue">
                        {operator[0]}(
                        {Array.isArray(operator[1])
                          ? (operator[1] as unknown[]).join(", ")
                          : String(operator[1])}
                        )
                      </Tag>
                    );
                  })}
                </Space>
              </Descriptions.Item>
            </Descriptions>
          ))}
        </Space>
      </Card>

      {/* ── Risk parameters ─────────────────────────────────────── */}
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

      {/* ── Validation flags ────────────────────────────────────── */}
      <Card size="small" title="Validation">
        <Space wrap>
          {Object.entries(validation).map(([key, value]) => (
            <Tag
              key={key}
              color={
                value === true
                  ? "green"
                  : value === false
                    ? "red"
                    : "default"
              }
            >
              {key.replace(/_/g, " ")}: {String(value)}
            </Tag>
          ))}
        </Space>
      </Card>

      {/* ── Audit timeline ──────────────────────────────────────── */}
      <AuditTimeline events={auditEvents} />

      {/* ── Version history ─────────────────────────────────────── */}
      <Card
        size="small"
        title="Version History"
        extra={
          <Tag>
            {versions.length} version{versions.length !== 1 ? "s" : ""}
          </Tag>
        }
      >
        <Table
          size="small"
          pagination={false}
          dataSource={versions.map((v, idx) => ({
            key: v.strategy_version_id,
            ...v,
            idx: idx + 1,
          }))}
          columns={[
            { title: "#", dataIndex: "idx", width: 40 },
            {
              title: "Version ID",
              dataIndex: "strategy_version_id",
              render: (id: string) => <Text code>{id}</Text>,
            },
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

      {/* ── Actions ─────────────────────────────────────────────── */}
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
