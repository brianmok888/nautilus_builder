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

export function addStrategyBlock(graph: StrategyGraphState, type: string): StrategyGraphState {
  if (!ALLOWED_STRATEGY_BLOCKS.includes(type as (typeof ALLOWED_STRATEGY_BLOCKS)[number])) {
    throw new Error("unsupported strategy block");
  }

  return {
    ...graph,
    nodes: [
      ...graph.nodes,
      {
        id: `node_${graph.nodes.length + 1}`,
        type: type as StrategyGraphNode["type"],
        params: {},
      },
    ],
  };
}

export function updateStrategyBlockParams(
  graph: StrategyGraphState,
  nodeId: string,
  params: Record<string, string | number | boolean>,
): StrategyGraphState {
  return {
    ...graph,
    nodes: graph.nodes.map((node) =>
      node.id === nodeId ? { ...node, params: { ...node.params, ...params } } : node,
    ),
  };
}

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
