"use client";

import { useMemo, useState } from "react";
import { Alert, Button, Card, Col, Descriptions, Form, Input, Row, Space, Tag, Typography } from "antd";
import { createBacktestJob, runBacktestJob } from "../../lib/api";
import type { BacktestJobStatus, BacktestRunResponse, RuntimeEvent } from "../../lib/types";

const DEFAULT_COMPILE_HASH = "a".repeat(64);
const SHA256_RE = /^[a-f0-9]{64}$/i;

type RunManifestDraft = {
  strategy_version_id: string;
  adapter_profile_id: string;
  instrument_id: string;
  validation_report_id: string;
  compile_hash: string;
  dataset_id: string;
  data_range: string;
  data_type: string;
  timeframe: string;
  market_type: string;
};

const defaultManifest: RunManifestDraft = {
  strategy_version_id: "sv_validated_001",
  adapter_profile_id: "BINANCE_PERP",
  instrument_id: "BTCUSDT-PERP",
  validation_report_id: "vr_validated_001",
  compile_hash: DEFAULT_COMPILE_HASH,
  dataset_id: "ds_binance_btcusdt_1m",
  data_range: "2024-01-01:2024-03-01",
  data_type: "historical_bars",
  timeframe: "1m",
  market_type: "crypto_perp",
};

function textValue(value: unknown, fallback = "pending"): string {
  if (value === undefined || value === null || value === "") return fallback;
  if (typeof value === "boolean") return value ? "true" : "false";
  return String(value);
}

function runTitle(response: BacktestRunResponse | null): string {
  const stage = response?.job?.stage ?? response?.job?.lifecycle_status ?? response?.job?.status ?? "pending";
  const normalized = String(stage).toLowerCase();
  if (normalized.includes("succeed")) return "BacktestNode run succeeded";
  if (normalized.includes("fail")) return "BacktestNode run failed";
  return `BacktestNode run ${stage}`;
}

function eventColor(event: RuntimeEvent): string {
  const stage = event.stage.toUpperCase();
  if (stage.includes("SUCCEEDED")) return "green";
  if (stage.includes("FAILED") || stage.includes("ERROR")) return "red";
  if (stage.includes("RUNNING")) return "blue";
  return "default";
}

function isTerminalJob(job: BacktestJobStatus | null): boolean {
  const state = `${job?.stage ?? ""} ${job?.lifecycle_status ?? ""} ${job?.status ?? ""}`.toLowerCase();
  return state.includes("succeed") || state.includes("fail") || state.includes("cancel");
}

export function BacktestLaunchPanel() {
  const [manifest, setManifest] = useState<RunManifestDraft>(defaultManifest);
  const [job, setJob] = useState<BacktestJobStatus | null>(null);
  const [runResult, setRunResult] = useState<BacktestRunResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [runError, setRunError] = useState<string | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [isRunning, setIsRunning] = useState(false);

  const missingFields = useMemo(
    () => Object.entries(manifest).filter(([, value]) => !value.trim()).map(([key]) => key),
    [manifest],
  );
  const compileHashValid = SHA256_RE.test(manifest.compile_hash.trim());
  const ready = missingFields.length === 0 && compileHashValid;
  const preview = useMemo(
    () => ({
      ...manifest,
      created_by: "builder_web",
      authority: {
        mode: "backtest_only",
        may_submit_order: false,
        browser_credentials: false,
      },
    }),
    [manifest],
  );
  const resultPayload = runResult?.result ?? {};
  const artifactRefs = runResult?.job.result_artifact_refs ?? job?.result_artifact_refs ?? {};
  const jobTerminal = isTerminalJob(job);
  const jobCardTitle = job ? (runResult ? `Job ${job.status}: ${job.job_id}` : `Job queued: ${job.job_id}`) : "Backtest job";

  function updateField(field: keyof RunManifestDraft, value: string) {
    setManifest((current) => ({ ...current, [field]: value }));
    setJob(null);
    setRunResult(null);
    setRunError(null);
  }

  async function onCreateJob() {
    if (!ready) return;
    setIsCreating(true);
    setError(null);
    setRunError(null);
    setJob(null);
    setRunResult(null);
    try {
      const created = await createBacktestJob({
        ...manifest,
        compile_hash: manifest.compile_hash.trim(),
        created_by: "builder_web",
      });
      setJob(created);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : String(caught));
    } finally {
      setIsCreating(false);
    }
  }

  async function onRunBacktestNode() {
    if (!job) return;
    setIsRunning(true);
    setRunError(null);
    setRunResult(null);
    try {
      const response = await runBacktestJob(job.job_id);
      setRunResult(response);
      setJob(response.job);
    } catch (caught) {
      setRunError(caught instanceof Error ? caught.message : String(caught));
    } finally {
      setIsRunning(false);
    }
  }

  return (
    <section className="panel backtest-launch-panel" aria-label="backtest launch panel">
      <Space orientation="vertical" size="middle" className="config-stack">
        <div>
          <Typography.Text className="hero-kicker">Backtest Center</Typography.Text>
          <Typography.Title level={3}>Validated run manifest</Typography.Title>
          <Typography.Paragraph type="secondary">
            Create a backend-owned Nautilus replay job only after StrategySpec validation,
            compile evidence, and catalog dataset selection are present.
          </Typography.Paragraph>
          <Space wrap>
            <Tag color="gold">may_submit_order: false</Tag>
            <Tag color="blue">manual promotion after review</Tag>
            <Tag color="green">dataset profile required</Tag>
            <Tag color="purple">backend_owned_backtestnode</Tag>
          </Space>
        </div>

        <Alert
          showIcon
          type="info"
          title="Backtest launch is evidence-only"
          description="The browser submits a run manifest to the backend job queue and can request the backend-owned BacktestNode replay trigger. It does not hold shell, worker, credential, or order authority."
        />

        <Card title="Run manifest" size="small">
          <Form layout="vertical" className="form-grid">
            <Form.Item label="Strategy version">
              <Input
                aria-label="Strategy version"
                value={manifest.strategy_version_id}
                onChange={(event) => updateField("strategy_version_id", event.target.value)}
              />
            </Form.Item>
            <Form.Item label="Validation report">
              <Input
                aria-label="Validation report"
                value={manifest.validation_report_id}
                onChange={(event) => updateField("validation_report_id", event.target.value)}
              />
            </Form.Item>
            <Form.Item
              label="Compile hash"
              validateStatus={compileHashValid ? undefined : "error"}
              help={compileHashValid ? undefined : "compile_hash must be a 64-character sha256 digest"}
            >
              <Input
                aria-label="Compile hash"
                value={manifest.compile_hash}
                onChange={(event) => updateField("compile_hash", event.target.value)}
              />
            </Form.Item>
            <Form.Item label="Adapter profile">
              <Input
                aria-label="Adapter profile"
                value={manifest.adapter_profile_id}
                onChange={(event) => updateField("adapter_profile_id", event.target.value)}
              />
            </Form.Item>
            <Form.Item label="Instrument">
              <Input
                aria-label="Instrument"
                value={manifest.instrument_id}
                onChange={(event) => updateField("instrument_id", event.target.value)}
              />
            </Form.Item>
            <Form.Item label="Dataset ID">
              <Input
                aria-label="Dataset ID"
                value={manifest.dataset_id}
                onChange={(event) => updateField("dataset_id", event.target.value)}
              />
            </Form.Item>
            <Form.Item label="Data range">
              <Input
                aria-label="Data range"
                value={manifest.data_range}
                onChange={(event) => updateField("data_range", event.target.value)}
              />
            </Form.Item>
            <Form.Item label="Data type">
              <Input
                aria-label="Data type"
                value={manifest.data_type}
                onChange={(event) => updateField("data_type", event.target.value)}
              />
            </Form.Item>
            <Form.Item label="Timeframe">
              <Input
                aria-label="Timeframe"
                value={manifest.timeframe}
                onChange={(event) => updateField("timeframe", event.target.value)}
              />
            </Form.Item>
            <Form.Item label="Market type">
              <Input
                aria-label="Market type"
                value={manifest.market_type}
                onChange={(event) => updateField("market_type", event.target.value)}
              />
            </Form.Item>
          </Form>
          {missingFields.length ? (
            <Alert
              showIcon
              type="warning"
              title={`Missing fields: ${missingFields.join(", ")}`}
            />
          ) : null}
          <Button type="primary" disabled={!ready} loading={isCreating} onClick={onCreateJob}>
            Create backtest job
          </Button>
        </Card>

        {error ? <Alert showIcon type="error" title="Backtest job creation failed" description={error} /> : null}

        {job ? (
          <Card title={jobCardTitle} size="small" aria-label="created backtest job">
            <Row gutter={[12, 12]}>
              <Col xs={24} lg={14}>
                <Descriptions column={1} size="small" bordered>
                  <Descriptions.Item label="Status">{job.status}</Descriptions.Item>
                  <Descriptions.Item label="Strategy version">{job.strategy_spec_version_id}</Descriptions.Item>
                  <Descriptions.Item label="Dataset">{job.dataset_id ?? manifest.dataset_id}</Descriptions.Item>
                  <Descriptions.Item label="Event stream">{job.event_stream_id ?? "pending"}</Descriptions.Item>
                  <Descriptions.Item label="Worker">{job.worker_id ?? "unassigned"}</Descriptions.Item>
                </Descriptions>
              </Col>
              <Col xs={24} lg={10}>
                <Space orientation="vertical" size="small">
                  <Typography.Text>Job state is backend-owned; review artifacts before manual promotion.</Typography.Text>
                  <Button onClick={onRunBacktestNode} loading={isRunning} disabled={isRunning || jobTerminal}>
                    Run BacktestNode
                  </Button>
                  <Typography.Text type="secondary">
                    Runs POST /api/backtest-jobs/{job.job_id}/run without StrategySpec payloads, catalog paths, worker commands, shell, or credentials from the browser.
                  </Typography.Text>
                  <a href={`/backtests/${job.job_id}`}>Open job console</a>
                </Space>
              </Col>
            </Row>
          </Card>
        ) : null}

        {runError ? <Alert showIcon type="error" title="BacktestNode run failed" description={runError} /> : null}

        {runResult ? (
          <Card title={runTitle(runResult)} size="small" aria-label="backtestnode run result">
            <Space orientation="vertical" size="small" className="config-stack">
              <Descriptions column={1} size="small" bordered>
                <Descriptions.Item label="Mode">{runResult.mode}</Descriptions.Item>
                <Descriptions.Item label="Engine mode">{textValue(resultPayload.engine_mode)}</Descriptions.Item>
                <Descriptions.Item label="Dataset source">{textValue(resultPayload.dataset_source)}</Descriptions.Item>
                <Descriptions.Item label="Catalog backed">{textValue(resultPayload.catalog_backed)}</Descriptions.Item>
              </Descriptions>
              <Space wrap>
                <Tag color="gold">orders: {textValue(resultPayload.orders, "0")}</Tag>
                <Tag color="gold">positions: {textValue(resultPayload.positions, "0")}</Tag>
                <Tag color="blue">execution_authority: {textValue(resultPayload.execution_authority, "false")}</Tag>
                <Tag color="blue">credentials_used: {textValue(resultPayload.credentials_used, "false")}</Tag>
              </Space>
              <div>
                <Typography.Text strong>Artifact manifest</Typography.Text>
                {Object.entries(artifactRefs).length ? (
                  <ul>
                    {Object.entries(artifactRefs).map(([key, value]) => (
                      <li key={key}>
                        <Typography.Text>{key}: </Typography.Text>
                        <Typography.Text code>{String(value)}</Typography.Text>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <Typography.Paragraph type="secondary">No artifact refs returned yet.</Typography.Paragraph>
                )}
              </div>
              <div>
                <Typography.Text strong>Runtime events</Typography.Text>
                {runResult.events.length ? (
                  <Space orientation="vertical" size="small">
                    {runResult.events.map((event, index) => (
                      <Space key={event.event_id ?? `${event.stage}-${index}`} wrap>
                        <Tag color={eventColor(event)}>{event.stage}</Tag>
                        <Typography.Text>{event.message ?? event.actor_id ?? "event"}</Typography.Text>
                        {typeof event.progress_pct === "number" ? (
                          <Typography.Text type="secondary">{event.progress_pct}%</Typography.Text>
                        ) : null}
                      </Space>
                    ))}
                  </Space>
                ) : (
                  <Typography.Paragraph type="secondary">No runtime events returned yet.</Typography.Paragraph>
                )}
              </div>
            </Space>
          </Card>
        ) : null}

        <Card title="Manifest preview" size="small" className="config-preview">
          <pre>{JSON.stringify(preview, null, 2)}</pre>
        </Card>
      </Space>
    </section>
  );
}
