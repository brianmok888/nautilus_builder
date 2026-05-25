import { AiStrategyCopilot } from "../components/ai-builder/AiStrategyCopilot";
import { PromotionRequestPanel } from "../components/promotions/PromotionRequestPanel";
import { StrategyBuilderWorkspace } from "../components/strategy-builder/StrategyBuilderWorkspace";
import { JobTerminal } from "../components/terminal/JobTerminal";

export default function HomePage() {
  return (
    <main className="app-shell">
      <section className="hero-card" aria-label="builder overview">
        <span className="hero-kicker">
          Builder-only / observational runtime
        </span>
        <h1>Nautilus Builder</h1>
        <p>
          Draft StrategySpecs, validate market data profiles, inspect backtest
          evidence, and request safe shadow promotion without granting the web
          UI live order authority.
        </p>
        <nav className="workflow-nav" aria-label="Operator workflow">
          <a href="/strategies">Strategies</a>
          <a href="/backtests/bt_job_001">Backtest job bt_job_001</a>
          <a href="/results/res_001">Results res_001</a>
        </nav>
      </section>
      <section className="dashboard-grid" aria-label="builder dashboard">
        <section className="card" aria-label="draft authoring">
          <span className="status-badge">Draft only</span>
          <h2>Strategy draft authoring</h2>
          <StrategyBuilderWorkspace />
        </section>
        <section className="terminal-card" aria-label="observational runtime">
          <span className="status-badge warning">Observational</span>
          <h2>Observational runtime console</h2>
          <p>{JobTerminal()}</p>
        </section>
        <section className="card" aria-label="advisory ai">
          <span className="status-badge warning">Advisory</span>
          <h2>Advisory AI drafting</h2>
          <AiStrategyCopilot />
        </section>
        <section className="card" aria-label="safe promotion">
          <span className="status-badge">Manual gate</span>
          <h2>Safe promotion request</h2>
          <PromotionRequestPanel />
        </section>
      </section>
    </main>
  );
}
