import { ValidationPanel } from "./ValidationPanel";

export const StrategyBuilderCanvas = () => {
  return (
    <section>
      <p>StrategyBuilderCanvas: draft authoring only; graph state serializes to StrategySpec.</p>
      <ValidationPanel errors={[]} />
    </section>
  );
};
