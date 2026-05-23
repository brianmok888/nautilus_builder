export const ALLOWED_STRATEGY_BLOCKS = ["EMA", "RSI", "crossed_above", "crossed_below", "gt", "lt"] as const;

export type StrategyGraphNode = {
  id: string;
  type: (typeof ALLOWED_STRATEGY_BLOCKS)[number];
  params: Record<string, string | number | boolean>;
};

export type StrategyGraphState = {
  nodes: StrategyGraphNode[];
  edges: Array<{ source: string; target: string }>;
};

export function graphToStrategySpec(graph: StrategyGraphState): Record<string, unknown> {
  const indicators = graph.nodes.filter((node) => node.type === "EMA" || node.type === "RSI");
  return {
    status: "draft",
    stage: "draft",
    indicators,
    graph_edges: graph.edges,
  };
}

export function strategySpecToGraph(spec: Record<string, unknown>): StrategyGraphState {
  const indicators = Array.isArray(spec.indicators) ? spec.indicators : [];
  return {
    nodes: indicators
      .filter((entry): entry is StrategyGraphNode => typeof entry === "object" && entry !== null && "type" in entry)
      .map((entry, index) => ({ id: entry.id ?? `node_${index + 1}`, type: entry.type, params: entry.params ?? {} })),
    edges: [],
  };
}
