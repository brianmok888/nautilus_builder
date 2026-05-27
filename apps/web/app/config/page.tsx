import { ExecutionLaneFeaturePanel } from "../../components/config/ExecutionLaneFeaturePanel";
import { ModelConfigTabs } from "../../components/config/ModelConfigTabs";

export default function ConfigPage() {
  return (
    <main className="app-shell">
      <section className="hero-card" aria-label="configuration overview">
        <span className="hero-kicker">Execution lane and model operations</span>
        <h1>Execution Lane / Config</h1>
        <p>
          Configure OpenAI-compatible model roles plus the backend-owned TradingNode
          paper/live lane. Credentials remain server-side and paper/live controls
          stay separate from strategy drafting.
        </p>
        <nav className="workflow-nav" aria-label="Configuration navigation">
          <a href="/">Strategy Builder</a>
          <a href="/backtests/bt_job_001">Backtest Center</a>
          <a href="/strategies">Strategy records</a>
        </nav>
      </section>
      <ModelConfigTabs />
      <ExecutionLaneFeaturePanel />
    </main>
  );
}
