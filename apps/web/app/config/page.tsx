import { ModelConfigTabs } from "../../components/config/ModelConfigTabs";

export default function ConfigPage() {
  return (
    <main className="app-shell">
      <section className="hero-card" aria-label="configuration overview">
        <span className="hero-kicker">Advisory model operations</span>
        <h1>Builder configuration</h1>
        <p>
          Configure LLM provider, model-role, guardrail, and audit settings for
          AI-assisted StrategySpec drafting without granting browser-side secret
          or live-trading authority.
        </p>
        <nav className="workflow-nav" aria-label="Configuration navigation">
          <a href="/">Builder dashboard</a>
          <a href="/strategies">Strategies</a>
        </nav>
      </section>
      <ModelConfigTabs />
    </main>
  );
}
