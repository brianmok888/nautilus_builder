import { StrategyDetailClient } from "../../../components/strategies/StrategyDetailClient";

export default async function StrategyDetailPage({
  params,
}: {
  params: Promise<{ strategyId: string }>;
}) {
  const { strategyId } = await params;
  return (
    <main className="app-shell">
      <StrategyDetailClient strategyId={strategyId} />
    </main>
  );
}
