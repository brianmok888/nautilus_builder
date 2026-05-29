import { StrategyListClient } from "../../components/strategies/StrategyListClient";

export default function StrategiesPage() {
  return (
    <main className="app-shell">
      <section className="hero-card">
        <h1>Strategy records</h1>
        <p>All strategies across every status. Edit draft/validated, clone, or send to Backtest Center.</p>
      </section>
      <StrategyListClient />
    </main>
  );
}
