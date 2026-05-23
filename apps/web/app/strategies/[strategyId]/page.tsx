import { StrategyDetailClient } from "../../../components/strategies/StrategyDetailClient";

export default async function StrategyDetailPage({ params }: { params: Promise<{ strategyId: string }> }) {
  const { strategyId } = await params;
  return (
    <main>
      <h1>Strategy {strategyId}</h1>
      <StrategyDetailClient strategyId={strategyId} />
    </main>
  );
}
