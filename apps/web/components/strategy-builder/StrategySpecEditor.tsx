export const StrategySpecEditor = ({ spec }: { spec?: Record<string, unknown> }) => {
  return (
    <section aria-label="strategy spec editor">
      <h3>StrategySpec editor</h3>
      {spec ? <pre>{JSON.stringify(spec, null, 2)}</pre> : null}
      <p>Draft JSON/YAML preview remains subject to backend validation and lifecycle gates.</p>
    </section>
  );
};
