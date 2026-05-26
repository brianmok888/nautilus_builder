import {
  cancelBacktestJob,
  fetchBacktestJob,
  fetchBacktestJobEvents,
} from "../../../lib/api";

export default async function BacktestJobPage({
  params,
}: {
  params: Promise<{ jobId: string }>;
}) {
  const { jobId } = await params;
  const contracts = [
    fetchBacktestJob.name,
    fetchBacktestJobEvents.name,
    cancelBacktestJob.name,
  ];
  return (
    <main className="app-shell backtest-center-shell">
      <section className="terminal-card">
        <p className="hero-kicker">Backtest Center</p>
        <h1>Backtest job {jobId}</h1>
        <h2>Observational runtime console</h2>
        <div className="dashboard-grid compact-backtest-grid">
          <section className="card" aria-label="run configuration">
            <h3>Run configuration</h3>
            <p>StrategySpec replay is evidence-only and selected catalog data remains backend validated.</p>
            <p>may_submit_order: false</p>
          </section>
          <section className="card" aria-label="job status">
            <h3>Job status</h3>
            <p>Job state, worker identity, and runtime events are read from backend contracts.</p>
          </section>
          <section className="card" aria-label="artifact manifest">
            <h3>Artifact manifest</h3>
            <p>Result JSON, report, logs, and future chart artifacts are linked after worker completion.</p>
          </section>
        </div>
        <p>Contracts: {contracts.join(", ")}</p>
        <p>
          <span className="status-badge warning">
            Allowed command: request cancel
          </span>
        </p>
        <p>Observational terminal: status, logs, metrics, and cancellation requests only.</p>
      </section>
    </main>
  );
}
