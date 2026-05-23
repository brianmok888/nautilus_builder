import type { ResultDashboardPayload } from "../../lib/types";

type ResultsDashboardProps = {
  resultId: string;
  payload?: ResultDashboardPayload;
};

const asRows = (value: Record<string, unknown>) => Object.entries(value).map(([key, item]) => ({ key, value: String(item) }));

const unknownRow = (row: unknown, index: number) => {
  if (row && typeof row === "object") {
    return Object.entries(row as Record<string, unknown>)
      .map(([key, value]) => `${key}: ${String(value)}`)
      .join(" | ");
  }
  return String(row);
};

export const ResultsDashboard = ({ resultId, payload }: ResultsDashboardProps) => {
  const metrics = payload ? asRows(payload.metrics) : [];
  const artifacts = payload ? asRows(payload.artifacts) : [];
  return (
    <section aria-label="observational results dashboard">
      <h2>Backtest results</h2>
      <p>Result: {resultId}</p>
      <p>Metrics and artifacts are observational only; no execution authority.</p>
      <nav aria-label="result tabs">
        <span>Summary</span>
        <span>Equity</span>
        <span>Trades</span>
        <span>Fills</span>
        <span>Logs</span>
        <span>Artifacts</span>
      </nav>
      {payload ? (
        <div>
          <section aria-label="metrics">
            <h3>Metrics</h3>
            <dl>
              {metrics.map((metric) => (
                <div key={metric.key}>
                  <dt>{metric.key}</dt>
                  <dd>{metric.value}</dd>
                </div>
              ))}
            </dl>
          </section>
          <section aria-label="trades">
            <h3>Trades</h3>
            {payload.trades.map((trade, index) => (
              <p key={index}>{unknownRow(trade, index)}</p>
            ))}
          </section>
          <section aria-label="fills">
            <h3>Fills</h3>
            {payload.fills.map((fill, index) => (
              <p key={index}>{unknownRow(fill, index)}</p>
            ))}
          </section>
          <section aria-label="logs">
            <h3>Logs</h3>
            {payload.logs.map((log, index) => (
              <p key={index}>{unknownRow(log, index)}</p>
            ))}
          </section>
          <section aria-label="artifacts">
            <h3>Artifacts</h3>
            <dl>
              {artifacts.map((artifact) => (
                <div key={artifact.key}>
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
