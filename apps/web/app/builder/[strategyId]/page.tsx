import { BuilderDashboard } from "../../../components/dashboard/BuilderDashboard";

export default async function BuilderStrategyPage({
  params,
}: {
  params: Promise<{ strategyId: string }>;
}) {
  const { strategyId } = await params;
  return (
    <div>
      <section className="hero-card" aria-label="strategy scoped builder">
        <span className="hero-kicker">StrategySpec Editor</span>
        <h1>Builder workspace for {strategyId}</h1>
        <p>
          This draft-only builder route opens strategy context without granting
          live trading authority or browser credential access.
        </p>
      </section>
      <BuilderDashboard />
    </div>
  );
}
