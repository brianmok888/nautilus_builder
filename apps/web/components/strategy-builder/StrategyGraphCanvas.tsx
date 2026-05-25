import type { StrategyGraphNode } from "../../lib/strategySpec";

export const StrategyGraphCanvas = ({
  nodes = [],
  onSelect,
}: {
  nodes?: StrategyGraphNode[];
  onSelect?: (nodeId: string) => void;
}) => {
  return (
    <section className="panel list-card" aria-label="strategy graph canvas">
      <p>
        Graph canvas serializes draft blocks into StrategySpec for backend
        validation.
      </p>
      <ul>
        {nodes.map((node) => (
          <li key={node.id}>
            <button type="button" onClick={() => onSelect?.(node.id)}>
              Select {node.type} {node.id}
            </button>
          </li>
        ))}
      </ul>
    </section>
  );
};
