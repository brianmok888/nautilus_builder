import { StrategyDetailClient } from "../../../components/strategies/StrategyDetailClient";

export default async function StrategyDetailPage({
  params,
}: {
  params: Promise<{ strategyId: string }>;
}) {
  const { strategyId } = await params;
  return (
    <main className="app-shell">
      <section className="hero-card">
        <h1>Strategy {strategyId}</h1>
      </section>
      <StrategyDetailClient strategyId={strategyId} />
    </main>
  );
}
