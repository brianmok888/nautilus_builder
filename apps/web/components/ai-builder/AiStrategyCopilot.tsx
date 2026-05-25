import { applyAiDraftToBuilder, generateAiDraft } from "../../lib/api";

export const AiStrategyCopilot = () => {
  const contracts = [generateAiDraft.name, applyAiDraftToBuilder.name];
  return (
    <section className="panel" aria-label="advisory ai copilot">
      <p>AiStrategyCopilot: advisory draft generation only</p>
      <p>
        ai_thread_id and improvement_cycle_id are required lane identifiers.
      </p>
      <p>
        strategy_lineage_id and strategy_version_id preserve Builder lineage
        during apply.
      </p>
      <button type="button">Apply to Builder</button>
      <p>Contracts: {contracts.join(", ")}</p>
    </section>
  );
};
