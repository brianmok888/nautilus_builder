"use client";

import type { ResultDashboardPayload } from "../../lib/types";
import {
  Card,
  Descriptions,
  Empty,
  Space,
  Statistic,
  Table,
  Tag,
  Typography,
} from "antd";
import { ArrowDownOutlined, ArrowUpOutlined } from "@ant-design/icons";

type ResultsDashboardProps = {
  resultId: string;
  payload?: ResultDashboardPayload;
};

function MetricValue({ label, value }: { label: string; value: unknown }) {
  const num = typeof value === "number" ? value : parseFloat(String(value));
  if (isNaN(num)) return <Tag>{String(value)}</Tag>;

  const isGood = label.toLowerCase().includes("return") || label.toLowerCase().includes("sharpe") || label.toLowerCase().includes("pnl");
  const isBad = label.toLowerCase().includes("drawdown");

  return (
    <Statistic
      title={label}
      value={num}
      precision={4}
      valueStyle={{ color: isBad ? "#cf1322" : num >= 0 ? "#3f8600" : "#cf1322" }}
      prefix={isGood && num >= 0 ? <ArrowUpOutlined /> : isBad || num < 0 ? <ArrowDownOutlined /> : undefined}
    />
  );
}

function ArtifactValue({ value }: { value: unknown }) {
  if (value === null || value === undefined || value === "") {
    return <Tag>Unavailable</Tag>;
  }
  return <Typography.Text code>{String(value)}</Typography.Text>;
}

export const ResultsDashboard = ({
  resultId,
  payload,
}: ResultsDashboardProps) => {
  if (!payload) {
    return (
      <Space orientation="vertical" style={{ width: "100%" }}>
        <Card>
          <p className="hero-kicker">Results / Research</p>
          <Typography.Title level={4}>Result: {resultId}</Typography.Title>
          <Tag color="orange">Observational</Tag>
          <Tag color="green">No execution authority</Tag>
        </Card>
        <Empty description="No result data available" />
      </Space>
    );
  }

  const metrics = payload.metrics ?? {};
  const metricEntries = Object.entries(metrics);

  return (
    <section className="app-shell" aria-label="observational results dashboard">
      <Space orientation="vertical" style={{ width: "100%" }} size="middle">
        {/* Header */}
        <Card>
          <p className="hero-kicker">Results / Research</p>
          <Typography.Title level={4}>Backtest results</Typography.Title>
          <p>Result: {resultId}</p>
          <p>
            <Tag color="orange">Observational</Tag>
            <span> Metrics and artifacts are observational only; execution capability is not present.</span>
          </p>
          <p><Tag color="green">No execution authority</Tag></p>
        </Card>

        {/* Key Metrics */}
        {metricEntries.length > 0 && (
          <Card title="Metric cards">
            <Space wrap size="large">
              {metricEntries.map(([key, value]) => (
                <MetricValue key={key} label={key} value={value} />
              ))}
            </Space>
          </Card>
        )}

        {/* Trades */}
        <Card title="Trades">
          {payload.trades.length === 0 ? (
            <Empty description="No trades" image={Empty.PRESENTED_IMAGE_SIMPLE} />
          ) : (
            <Table
              dataSource={payload.trades.map((t, i) => ({ ...((t as Record<string, unknown>) ?? {}), _key: i }))}
              rowKey="_key"
              pagination={false}
              size="small"
              columns={Object.keys(payload.trades[0] as Record<string, unknown> ?? {}).map((col) => ({
                title: col,
                dataIndex: col,
                key: col,
                render: (val: unknown) => <Typography.Text>{String(val)}</Typography.Text>,
              }))}
            />
          )}
        </Card>

        {/* Fills */}
        <Card title="Fills">
          {payload.fills.length === 0 ? (
            <Empty description="No fills" image={Empty.PRESENTED_IMAGE_SIMPLE} />
          ) : (
            <Table
              dataSource={payload.fills.map((f, i) => ({ ...((f as Record<string, unknown>) ?? {}), _key: i }))}
              rowKey="_key"
              pagination={false}
              size="small"
              columns={Object.keys(payload.fills[0] as Record<string, unknown> ?? {}).map((col) => ({
                title: col,
                dataIndex: col,
                key: col,
                render: (val: unknown) => <Typography.Text>{String(val)}</Typography.Text>,
              }))}
            />
          )}
        </Card>

        {/* Logs */}
        <Card title="Logs">
          {payload.logs.length === 0 ? (
            <Empty description="No logs" image={Empty.PRESENTED_IMAGE_SIMPLE} />
          ) : (
            <Table
              dataSource={payload.logs.map((l, i) => ({ ...((l as Record<string, unknown>) ?? {}), _key: i }))}
              rowKey="_key"
              pagination={false}
              size="small"
              columns={Object.keys(payload.logs[0] as Record<string, unknown> ?? {}).map((col) => ({
                title: col,
                dataIndex: col,
                key: col,
                render: (val: unknown) => <Typography.Text>{String(val)}</Typography.Text>,
              }))}
            />
          )}
        </Card>

        {/* Research Charts */}
        <Card title="Research charts">
          <h3>Equity curve placeholder</h3>
          <p className="muted">chart library later: wire equity curve after a chart package is deliberately selected.</p>
          <h3>Drawdown placeholder</h3>
          <p className="muted">Drawdown placeholder remains static until result artifacts provide chart-ready series.</p>
          <h3>Research notes</h3>
          <p className="muted">Capture hypothesis, dataset scope, and follow-up optimizer ideas without execution authority.</p>
        </Card>

        {/* Report Summary */}
        {payload.report_summary && (
          <Card title="Report Summary">
            <Descriptions column={1} size="small" bordered>
              <Descriptions.Item label="Sections">
                {(payload.report_summary.sections ?? []).join(" → ")}
              </Descriptions.Item>
              <Descriptions.Item label="Chart Sections">
                {(payload.report_summary.chart_sections ?? []).join(" → ") || "None"}
              </Descriptions.Item>
              <Descriptions.Item label="Execution Authority">
                <Tag color="green">Disabled — observational only</Tag>
              </Descriptions.Item>
            </Descriptions>
          </Card>
        )}

        {/* Artifacts */}
        {payload.artifacts && Object.keys(payload.artifacts).length > 0 && (
          <Card title="Artifacts">
            <Descriptions column={1} size="small" bordered>
              {Object.entries(payload.artifacts).map(([key, value]) => (
                <Descriptions.Item key={key} label={key}>
                  <ArtifactValue value={value} />
                </Descriptions.Item>
              ))}
            </Descriptions>
          </Card>
        )}
      </Space>
    </section>
  );
};
