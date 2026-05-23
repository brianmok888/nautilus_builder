export default function StrategyDetailPage({ params }: { params: { strategyId: string } }) {
  return (
    <main>
      <h1>Strategy {params.strategyId}</h1>
      <h2>Version history</h2>
      <p>strategy_lineage_id is the backend identity anchor.</p>
      <a href={`/builder/${params.strategyId}`}>Open in Builder</a>
      <p>Version history and validation state are observational until backend mutation is requested.</p>
    </main>
  );
}
