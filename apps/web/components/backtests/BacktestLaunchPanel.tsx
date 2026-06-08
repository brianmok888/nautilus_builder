"use client";

import Link from "next/link";

import { useEffect, useMemo, useState } from "react";
import { Alert, Button, Descriptions, Input, Space, Tag, Typography } from "antd";
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

export function BacktestLaunchPanel({ strategy }: { strategy?: { strategy_id: string; latest_spec: Record<string, unknown> } | null }) {
  const [manifest, setManifest] = useState<RunManifestDraft>(defaultManifest);
  const [job, setJob] = useState<BacktestJobStatus | null>(null);
  const [runResult, setRunResult] = useState<BacktestRunResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [runError, setRunError] = useState<string | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [isRunning, setIsRunning] = useState(false);

  // Auto-fill manifest from selected strategy
  useEffect(() => {
    if (!strategy) return;
    const spec = strategy.latest_spec || {};
    setManifest((prev) => ({
      ...prev,
      strategy_version_id: strategy.strategy_id,
      adapter_profile_id: String(spec.adapter_id ?? prev.adapter_profile_id),
      instrument_id: String(spec.instrument_id ?? prev.instrument_id),
      market_type: String((spec as Record<string, unknown>).venue === "BINANCE" ? "crypto_perp" : prev.market_type),
    }));
    setJob(null);
    setRunResult(null);
    setRunError(null);
  }, [strategy]);

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

        {/* Run manifest — uses manifest-section + manifest-form-grid layout */}
        <section className="manifest-section">
          <div className="manifest-section-header">
            <h3>Run manifest</h3>
          </div>

          <div className="manifest-form-grid">
            <div className="manifest-form-field">
              <label htmlFor="manifest-strategy-version">Strategy version</label>
              <Input
                id="manifest-strategy-version"
                aria-label="Strategy version"
                value={manifest.strategy_version_id}
                onChange={(event) => updateField("strategy_version_id", event.target.value)}
              />
            </div>

            <div className="manifest-form-field">
              <label htmlFor="manifest-validation-report">Validation report</label>
              <Input
                id="manifest-validation-report"
                aria-label="Validation report"
                value={manifest.validation_report_id}
                onChange={(event) => updateField("validation_report_id", event.target.value)}
              />
            </div>

            <div className="manifest-form-field">
              <label htmlFor="manifest-compile-hash">Compile hash</label>
              <Input
                id="manifest-compile-hash"
                aria-label="Compile hash"
                className="hash-field"
                value={manifest.compile_hash}
                status={compileHashValid ? undefined : "error"}
                onChange={(event) => updateField("compile_hash", event.target.value)}
              />
              {!compileHashValid ? (
                <Typography.Text type="danger" style={{ fontSize: 12, display: "block", marginTop: 4 }}>
                  compile_hash must be a 64-character sha256 digest
                </Typography.Text>
              ) : null}
            </div>

            <div className="manifest-form-field">
              <label htmlFor="manifest-adapter-profile">Adapter profile</label>
              <Input
                id="manifest-adapter-profile"
                aria-label="Adapter profile"
                value={manifest.adapter_profile_id}
                onChange={(event) => updateField("adapter_profile_id", event.target.value)}
              />
            </div>

            <div className="manifest-form-field">
              <label htmlFor="manifest-instrument">Instrument</label>
              <Input
                id="manifest-instrument"
                aria-label="Instrument"
                value={manifest.instrument_id}
                onChange={(event) => updateField("instrument_id", event.target.value)}
              />
            </div>

            <div className="manifest-form-field">
              <label htmlFor="manifest-dataset-id">Dataset ID</label>
              <Input
                id="manifest-dataset-id"
                aria-label="Dataset ID"
                value={manifest.dataset_id}
                onChange={(event) => updateField("dataset_id", event.target.value)}
              />
            </div>

            <div className="manifest-form-field">
              <label htmlFor="manifest-data-range">Data range</label>
              <Input
                id="manifest-data-range"
                aria-label="Data range"
                value={manifest.data_range}
                onChange={(event) => updateField("data_range", event.target.value)}
              />
            </div>

            <div className="manifest-form-field">
              <label htmlFor="manifest-data-type">Data type</label>
              <Input
                id="manifest-data-type"
                aria-label="Data type"
                value={manifest.data_type}
                onChange={(event) => updateField("data_type", event.target.value)}
              />
            </div>

            <div className="manifest-form-field">
              <label htmlFor="manifest-timeframe">Timeframe</label>
              <Input
                id="manifest-timeframe"
                aria-label="Timeframe"
                value={manifest.timeframe}
                onChange={(event) => updateField("timeframe", event.target.value)}
              />
            </div>

            <div className="manifest-form-field">
              <label htmlFor="manifest-market-type">Market type</label>
              <Input
                id="manifest-market-type"
                aria-label="Market type"
                value={manifest.market_type}
                onChange={(event) => updateField("market_type", event.target.value)}
              />
            </div>
          </div>

          {missingFields.length ? (
            <Alert
              showIcon
              type="warning"
              title={`Missing fields: ${missingFields.join(", ")}`}
            />
          ) : null}

          <div>
            <Button type="primary" disabled={!ready} loading={isCreating} onClick={onCreateJob}>
              Create backtest job
            </Button>
          </div>
        </section>

        {error ? <Alert showIcon type="error" title="Backtest job creation failed" description={error} /> : null}

        {job ? (
          <section className="manifest-section" aria-label="created backtest job">
            <div className="manifest-section-header">
              <h3>{jobCardTitle}</h3>
            </div>
            <Descriptions column={{ xs: 1, sm: 2, lg: 3 }} size="small" bordered>
              <Descriptions.Item label="Status">{job.status}</Descriptions.Item>
              <Descriptions.Item label="Strategy version">{job.strategy_spec_version_id}</Descriptions.Item>
              <Descriptions.Item label="Dataset">{job.dataset_id ?? manifest.dataset_id}</Descriptions.Item>
              <Descriptions.Item label="Event stream">{job.event_stream_id ?? "pending"}</Descriptions.Item>
              <Descriptions.Item label="Worker">{job.worker_id ?? "unassigned"}</Descriptions.Item>
            </Descriptions>
            <Space orientation="vertical" size="small">
              <Typography.Text>Job state is backend-owned; review artifacts before manual promotion.</Typography.Text>
              <Button onClick={onRunBacktestNode} loading={isRunning} disabled={isRunning || jobTerminal}>
                Run BacktestNode
              </Button>
              <Typography.Text type="secondary">
                Runs POST /api/backtest-jobs/{job.job_id}/run without StrategySpec payloads, catalog paths, worker commands, shell, or credentials from the browser.
              </Typography.Text>
              <Link href={`/backtests/${job.job_id}`}>Open job console</Link>
            </Space>
          </section>
        ) : null}

        {runError ? <Alert showIcon type="error" title="BacktestNode run failed" description={runError} /> : null}

        {runResult ? (
          <section className="manifest-section" aria-label="backtestnode run result">
            <div className="manifest-section-header">
              <h3>{runTitle(runResult)}</h3>
            </div>
            <Space orientation="vertical" size="small" className="config-stack">
              <Descriptions column={{ xs: 1, sm: 2, lg: 3 }} size="small" bordered>
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
          </section>
        ) : null}

        {/* Manifest preview — uses manifest-section + manifest-preview */}
        <section className="manifest-section">
          <div className="manifest-section-header">
            <h3>Manifest preview</h3>
          </div>
          <div className="manifest-preview">
            <pre>{JSON.stringify(preview, null, 2)}</pre>
          </div>
        </section>
      </Space>
    </section>
  );
}
