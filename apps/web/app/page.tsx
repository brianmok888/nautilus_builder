import { AiStrategyCopilot } from "../components/ai-builder/AiStrategyCopilot";
import { PromotionRequestPanel } from "../components/promotions/PromotionRequestPanel";
import { StrategyBuilderWorkspace } from "../components/strategy-builder/StrategyBuilderWorkspace";
import { JobTerminal } from "../components/terminal/JobTerminal";

export default function HomePage() {
  return (
    <main>
      <h1>Nautilus Builder</h1>
      <section aria-label="draft authoring">
        <h2>Strategy draft authoring</h2>
        <StrategyBuilderWorkspace />
      </section>
      <section aria-label="observational runtime">
        <h2>Observational runtime console</h2>
        <JobTerminal />
      </section>
      <section aria-label="advisory ai">
        <h2>Advisory AI drafting</h2>
        <AiStrategyCopilot />
      </section>
      <section aria-label="safe promotion">
        <h2>Safe promotion request</h2>
        <PromotionRequestPanel />
      </section>
    </main>
  );
}
