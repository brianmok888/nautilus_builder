import { ValidationPanel } from "./ValidationPanel";

export const StrategyBuilderCanvas = () => {
  return (
    <section className="panel">
      <p>
        StrategyBuilderCanvas: draft authoring only; graph state serializes to
        StrategySpec.
      </p>
      <ValidationPanel errors={[]} />
    </section>
  );
};
