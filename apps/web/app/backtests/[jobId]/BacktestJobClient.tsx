"use client";

import { useState } from "react";
import { Alert, Button, Card, Descriptions, Space, Tag, Typography } from "antd";
import { cancelBacktestJob } from "../../../lib/api";
import type { BacktestJobEvents, BacktestJobStatus } from "../../../lib/types";

type BacktestEvent = {
  event_id?: string;
  stage?: string;
  level?: string;
  message?: string;
  actor_id?: string;
  timestamp?: string;
  metadata?: Record<string, unknown>;
};

export function BacktestJobClient({
  initialJob,
  initialEvents,
}: {
  initialJob: BacktestJobStatus;
  initialEvents: BacktestJobEvents;
}) {
  const [job, setJob] = useState(initialJob);
  const [isCanceling, setIsCanceling] = useState(false);
  const [cancelError, setCancelError] = useState<string | null>(null);

  async function onRequestCancel() {
    setIsCanceling(true);
    setCancelError(null);
    try {
      const canceled = await cancelBacktestJob(job.job_id);
      setJob((current) => ({ ...current, ...canceled }));
    } catch (error) {
      setCancelError(error instanceof Error ? error.message : String(error));
    } finally {
      setIsCanceling(false);
    }
  }

  const cancelRequested = Boolean(job.cancel_requested) || job.status === "cancel_requested";
  const artifacts = Object.entries(job.result_artifact_refs ?? {});
  const events = initialEvents.events.map(normalizeEvent);

  return (
    <section className="terminal-card" aria-label="backtest job detail">
      <Space orientation="vertical" size="middle" className="config-stack">
        <div>
          <p className="hero-kicker">Backtest Center</p>
          <Typography.Title level={1}>Backtest job {job.job_id}</Typography.Title>
          <Typography.Title level={2}>Observational runtime console</Typography.Title>
          <Space wrap>
            <Tag color={cancelRequested ? "orange" : "blue"}>{job.status}</Tag>
            <Tag color="default">{job.mode ?? "backend_owned"}</Tag>
            <Tag color="gold">may_submit_order: false</Tag>
          </Space>
        </div>

        <Alert
          showIcon
          type="info"
          title="Backtest-only control surface"
          description="This page reads backend-owned job contracts, event streams, and artifact refs. The only browser action is an observational cancellation request."
        />
        <Typography.Paragraph>Allowed command: request cancel. Observational terminal only.</Typography.Paragraph>

        <div className="dashboard-grid compact-backtest-grid">
          <Card title="Run configuration" aria-label="run configuration">
            <Descriptions column={1} size="small" bordered>
              <Descriptions.Item label="Strategy version">{job.strategy_spec_version_id ?? "unknown"}</Descriptions.Item>
              <Descriptions.Item label="Adapter profile">{job.adapter_profile_id ?? "unknown"}</Descriptions.Item>
              <Descriptions.Item label="Instrument">{job.instrument_id ?? "unknown"}</Descriptions.Item>
              <Descriptions.Item label="Data range">{job.data_range ?? "unknown"}</Descriptions.Item>
              <Descriptions.Item label="Data type">{job.data_type ?? "unknown"}</Descriptions.Item>
              <Descriptions.Item label="Timeframe">{job.timeframe ?? "unknown"}</Descriptions.Item>
            </Descriptions>
          </Card>

          <Card title="Job status" aria-label="job status">
            <Descriptions column={1} size="small" bordered>
              <Descriptions.Item label="Status">{job.status}</Descriptions.Item>
              <Descriptions.Item label="Stage">{job.stage ?? job.lifecycle_status ?? "unknown"}</Descriptions.Item>
              <Descriptions.Item label="Worker">{job.worker_id ?? "unassigned"}</Descriptions.Item>
              <Descriptions.Item label="Created by">{job.created_by ?? "unknown"}</Descriptions.Item>
              <Descriptions.Item label="Updated">{job.updated_at ?? "unknown"}</Descriptions.Item>
              <Descriptions.Item label="Cancel requested">{String(cancelRequested)}</Descriptions.Item>
            </Descriptions>
            <Button
              danger
              disabled={cancelRequested}
              loading={isCanceling}
              onClick={onRequestCancel}
              style={{ marginTop: 12 }}
            >
              Request cancel
            </Button>
            {cancelError ? <Alert showIcon type="error" title="Cancel request failed" description={cancelError} /> : null}
          </Card>

          <Card title="Artifact manifest" aria-label="artifact manifest">
            {artifacts.length ? (
              <ul className="config-checklist">
                {artifacts.map(([name, ref]) => (
                  <li key={name}>
                    <Typography.Text strong>{name}</Typography.Text>
                    <Typography.Text code>{ref}</Typography.Text>
                  </li>
                ))}
              </ul>
            ) : (
              <Typography.Text type="secondary">No result artifacts have been reported yet.</Typography.Text>
            )}
          </Card>
        </div>

        <Card title="Runtime event stream" aria-label="runtime event stream">
          <Typography.Paragraph>
            <Typography.Text strong>Stream:</Typography.Text> {initialEvents.stream_name ?? job.event_stream_id ?? "unknown"}
          </Typography.Paragraph>
          {events.length ? (
            <ul className="config-checklist">
              {events.map((event, index) => (
                <li key={event.event_id ?? index}>
                  <Space orientation="vertical" size={2}>
                    <Space wrap>
                      <Tag>{event.level ?? "INFO"}</Tag>
                      <Typography.Text>{event.stage ?? "UNKNOWN"}</Typography.Text>
                      <Typography.Text type="secondary">{event.actor_id ?? "unknown actor"}</Typography.Text>
                    </Space>
                    <Typography.Text>{event.message ?? "event received"}</Typography.Text>
                    {event.timestamp ? <Typography.Text type="secondary">{event.timestamp}</Typography.Text> : null}
                  </Space>
                </li>
              ))}
            </ul>
          ) : (
            <Typography.Text type="secondary">No runtime events are available for this job yet.</Typography.Text>
          )}
        </Card>
      </Space>
    </section>
  );
}

function normalizeEvent(event: unknown): BacktestEvent {
  if (typeof event !== "object" || event === null) return { message: String(event) };
  return event as BacktestEvent;
}
