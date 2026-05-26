import {
  fetchBacktestJob,
  fetchBacktestJobEvents,
} from "../../../lib/api";
import type { BacktestJobEvents, BacktestJobStatus } from "../../../lib/types";
import { BacktestJobClient } from "./BacktestJobClient";

export default async function BacktestJobPage({
  params,
}: {
  params: Promise<{ jobId: string }>;
}) {
  const { jobId } = await params;
  const { job, events } = await loadBacktestContracts(jobId);

  return (
    <main className="app-shell backtest-center-shell">
      <BacktestJobClient initialJob={job} initialEvents={events} />
    </main>
  );
}

async function loadBacktestContracts(jobId: string): Promise<{
  job: BacktestJobStatus;
  events: BacktestJobEvents;
}> {
  try {
    const [job, events] = await Promise.all([
      fetchBacktestJob(jobId),
      fetchBacktestJobEvents(jobId),
    ]);
    return { job, events };
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    return {
      job: fallbackBacktestJob(jobId),
      events: {
        job_id: jobId,
        stream_name: `builder:runtime:${jobId}`,
        status: "degraded",
        mode: "observational",
        events: [
          {
            event_id: `${jobId}_evt_backend_unavailable`,
            stage: "OBSERVING",
            level: "WARNING",
            message: `Backend job contract unavailable: ${message}`,
            actor_id: "builder-web",
            timestamp: "degraded-mode",
            metadata: { degraded: true },
          },
        ],
      },
    };
  }
}

function fallbackBacktestJob(jobId: string): BacktestJobStatus {
  return {
    job_id: jobId,
    status: "observing",
    stage: "OBSERVING",
    lifecycle_status: "OBSERVING",
    created_by: "builder-web",
    updated_at: "degraded-mode",
    strategy_spec_version_id: "unknown",
    adapter_profile_id: "unknown",
    instrument_id: "unknown",
    data_range: "unknown",
    data_type: "unknown",
    timeframe: "unknown",
    worker_id: "unassigned",
    result_artifact_refs: {},
    event_stream_id: `builder:runtime:${jobId}`,
    cancel_requested: false,
    mode: "observational_fallback",
  };
}
