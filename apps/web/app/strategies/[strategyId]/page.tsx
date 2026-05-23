export default async function StrategyDetailPage({ params }: { params: Promise<{ strategyId: string }> }) {
  const { strategyId } = await params;
  return (
    <main>
      <h1>Strategy {strategyId}</h1>
      <h2>Version history</h2>
      <p>strategy_lineage_id is the backend identity anchor.</p>
      <a href={`/builder/${strategyId}`}>Open in Builder</a>
      <p>Version history and validation state are observational until backend mutation is requested.</p>
    </main>
  );
}
