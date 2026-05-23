export const ResultsDashboard = ({ resultId }: { resultId: string }) => {
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
    </section>
  );
};
