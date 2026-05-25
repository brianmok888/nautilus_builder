import type { StrategyGraphNode } from "../../lib/strategySpec";

export const BlockInspector = ({
  selectedNode,
  onChangeParams,
}: {
  selectedNode?: StrategyGraphNode;
  onChangeParams?: (params: Record<string, number>) => void;
}) => {
  return (
    <aside className="panel" aria-label="block inspector">
      <h3>Inspector</h3>
      {selectedNode ? (
        <p>Selected block: {selectedNode.type}</p>
      ) : (
        <p>No block selected.</p>
      )}
      <label>
        period
        <input
          aria-label="period"
          type="number"
          value={Number(selectedNode?.params.period ?? 0)}
          onChange={(event) =>
            onChangeParams?.({ period: Number(event.target.value) })
          }
        />
      </label>
      <p>
        Block params are draft-only until backend validation accepts the
        StrategySpec.
      </p>
    </aside>
  );
};
