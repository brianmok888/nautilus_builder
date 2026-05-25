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
    <main className="app-shell">
      <section className="terminal-card">
        <h1>Backtest job {jobId}</h1>
        <h2>Observational runtime console</h2>
        <p>Contracts: {contracts.join(", ")}</p>
        <p>
          <span className="status-badge warning">
            Allowed command: request cancel
          </span>
        </p>
      </section>
    </main>
  );
}
