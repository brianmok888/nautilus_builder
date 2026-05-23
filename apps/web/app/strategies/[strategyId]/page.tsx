export default function StrategyDetailPage({ params }: { params: { strategyId: string } }) {
  return (
    <main>
      <h1>Strategy {params.strategyId}</h1>
      <p>Version history and validation state are observational until backend mutation is requested.</p>
    </main>
  );
}
