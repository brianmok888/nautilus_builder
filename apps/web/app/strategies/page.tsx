import { StrategyListClient } from "../../components/strategies/StrategyListClient";

export default function StrategiesPage() {
  return (
    <main className="app-shell">
      <section className="hero-card">
        <h1>Strategy list</h1>
        <p>Saved StrategySpec drafts and versions are backend-owned records.</p>
      </section>
      <StrategyListClient />
    </main>
  );
}
