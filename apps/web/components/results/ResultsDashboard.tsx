import type { ResultDashboardPayload } from "../../lib/types";

type ResultsDashboardProps = {
  resultId: string;
  payload?: ResultDashboardPayload;
};

const asRows = (value: Record<string, unknown>) =>
  Object.entries(value).map(([key, item]) => ({ key, value: String(item) }));

const unknownRow = (row: unknown, index: number) => {
  if (row && typeof row === "object") {
    return Object.entries(row as Record<string, unknown>)
      .map(([key, value]) => `${key}: ${String(value)}`)
      .join(" | ");
  }
  return String(row);
};

export const ResultsDashboard = ({
  resultId,
  payload,
}: ResultsDashboardProps) => {
  const reportSummary = payload?.report_summary;
  const metrics = payload ? asRows({ ...(reportSummary?.metrics ?? {}), ...payload.metrics }) : [];
  const artifacts = payload ? asRows(payload.artifacts) : [];
  const sectionTrail = reportSummary?.sections?.join(" → ") ?? "";
  const chartTrail = reportSummary?.chart_sections?.join(" → ") ?? "";
  return (
    <section className="app-shell" aria-label="observational results dashboard">
      <h2>Backtest results</h2>
      <p>Result: {resultId}</p>
      <p>
        <span className="status-badge warning">Observational</span> Metrics and
        artifacts are observational only; execution capability is not present.
      </p>
      <nav className="result-tabs" aria-label="result tabs">
        <span>Summary</span>
        <span>Equity</span>
        <span>Trades</span>
        <span>Fills</span>
        <span>Logs</span>
        <span>Artifacts</span>
      </nav>
      {payload ? (
        <div className="dashboard-grid">
          <section className="card" aria-label="metrics">
            <h3>Metrics</h3>
            <dl className="metric-grid">
              {metrics.map((metric) => (
                <div key={metric.key}>
                  <dt>{metric.key}</dt>
                  <dd>{metric.value}</dd>
                </div>
              ))}
            </dl>
          </section>
          <section className="card" aria-label="trades">
            <h3>Trades</h3>
            {payload.trades.map((trade, index) => (
              <p key={index}>{unknownRow(trade, index)}</p>
            ))}
          </section>
          <section className="card" aria-label="fills">
            <h3>Fills</h3>
            {payload.fills.map((fill, index) => (
              <p key={index}>{unknownRow(fill, index)}</p>
            ))}
          </section>
          <section className="card" aria-label="logs">
            <h3>Logs</h3>
            {payload.logs.map((log, index) => (
              <p key={index}>{unknownRow(log, index)}</p>
            ))}
          </section>
          {reportSummary ? (
            <section className="card" aria-label="report summary">
              <h3>Report sections</h3>
              <p className="muted">{sectionTrail}</p>
              <h3>Chart metadata</h3>
              <p className="muted">{chartTrail || "No chart sections"}</p>
              <p>
                <span className="status-badge success">No execution authority</span>
              </p>
            </section>
          ) : null}
          <section className="card" aria-label="artifacts">
            <h3>Artifacts</h3>
            <dl className="metric-grid">
              {artifacts.map((artifact) => (
                <div className="artifact-row" key={artifact.key}>
                  <dt>{artifact.key}</dt>
                  <dd>{artifact.value}</dd>
                </div>
              ))}
            </dl>
          </section>
        </div>
      ) : null}
    </section>
  );
};
