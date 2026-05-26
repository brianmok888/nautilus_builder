export const ALLOWED_STRATEGY_BLOCKS = ["EMA", "SMA", "RSI", "MACD", "ATR", "BollingerBands", "VWAP", "crossed_above", "crossed_below", "gt", "lt", "gte", "lte", "eq"] as const;

const INDICATOR_BLOCKS = ["EMA", "SMA", "RSI", "MACD", "ATR", "BollingerBands", "VWAP"] as const;

type IndicatorBlockType = (typeof INDICATOR_BLOCKS)[number];

export type StrategyGraphNode = {
  id: string;
  type: (typeof ALLOWED_STRATEGY_BLOCKS)[number];
  params: Record<string, string | number | boolean>;
};

export type StrategyGraphState = {
  nodes: StrategyGraphNode[];
  edges: Array<{ source: string; target: string }>;
};

type IndicatorSpec = {
  type: IndicatorBlockType;
  input: "close";
  period: number;
};

type StrategySpecDraft = {
  schema_version: "1.0.0";
  version: "0.1.0-draft.1";
  stage: "draft";
  status: "draft";
  created_from: "user";
  is_frozen: false;
  adapter_id: "BINANCE_PERP";
  venue: "BINANCE";
  instrument_id: "BTCUSDT-PERP";
  bar_type: "BTCUSDT-PERP.BINANCE-5-MINUTE-LAST-EXTERNAL";
  data_range: { start: "2025-01-01T00:00:00Z"; end: "2025-06-01T00:00:00Z" };
  indicators: Record<string, IndicatorSpec>;
  rules: {
    long_entry: { all: Array<{ crossed_above: ["ema_fast", "ema_slow"] } | { gt: ["rsi", 52] }> };
    long_exit: { any: Array<{ crossed_below: ["ema_fast", "ema_slow"] } | { lt: ["rsi", 45] }> };
  };
  risk: {
    position_size_pct: 0.05;
    stop_loss_pct: 0.012;
    take_profit_pct: 0.024;
    max_hold_bars: 48;
  };
  validation: {
    bar_close_only: true;
    no_lookahead_required: true;
    requires_backtest_before_shadow: true;
    output_mode: "signal_preview_only";
  };
  provenance: { created_by: "user"; parent_version_id: null };
};

const DEFAULT_INDICATORS: Record<string, IndicatorSpec> = {
  ema_fast: { type: "EMA", input: "close", period: 20 },
  ema_slow: { type: "EMA", input: "close", period: 50 },
  rsi: { type: "RSI", input: "close", period: 14 },
};

const BASE_STRATEGY_SPEC: Omit<StrategySpecDraft, "indicators"> = {
  schema_version: "1.0.0",
  version: "0.1.0-draft.1",
  stage: "draft",
  status: "draft",
  created_from: "user",
  is_frozen: false,
  adapter_id: "BINANCE_PERP",
  venue: "BINANCE",
  instrument_id: "BTCUSDT-PERP",
  bar_type: "BTCUSDT-PERP.BINANCE-5-MINUTE-LAST-EXTERNAL",
  data_range: {
    start: "2025-01-01T00:00:00Z",
    end: "2025-06-01T00:00:00Z",
  },
  rules: {
    long_entry: { all: [{ crossed_above: ["ema_fast", "ema_slow"] }, { gt: ["rsi", 52] }] },
    long_exit: { any: [{ crossed_below: ["ema_fast", "ema_slow"] }, { lt: ["rsi", 45] }] },
  },
  risk: {
    position_size_pct: 0.05,
    stop_loss_pct: 0.012,
    take_profit_pct: 0.024,
    max_hold_bars: 48,
  },
  validation: {
    bar_close_only: true,
    no_lookahead_required: true,
    requires_backtest_before_shadow: true,
    output_mode: "signal_preview_only",
  },
  provenance: { created_by: "user", parent_version_id: null },
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
  return {
    ...BASE_STRATEGY_SPEC,
    indicators: indicatorsFromGraph(graph),
  } satisfies StrategySpecDraft;
}

export function strategySpecToGraph(spec: Record<string, unknown>): StrategyGraphState {
  const indicators = indicatorEntries(spec.indicators);
  return {
    nodes: indicators.map(([id, indicator]) => ({
      id,
      type: indicator.type,
      params: { input: indicator.input, period: indicator.period },
    })),
    edges: [],
  };
}

function indicatorsFromGraph(graph: StrategyGraphState): Record<string, IndicatorSpec> {
  const indicators: Record<string, IndicatorSpec> = cloneDefaultIndicators();
  const emaNodes = indicatorNodes(graph, "EMA");
  const rsiNodes = indicatorNodes(graph, "RSI");

  if (emaNodes[0]) indicators.ema_fast = indicatorFromNode(emaNodes[0], indicators.ema_fast);
  if (emaNodes[1]) indicators.ema_slow = indicatorFromNode(emaNodes[1], indicators.ema_slow);
  if (rsiNodes[0]) indicators.rsi = indicatorFromNode(rsiNodes[0], indicators.rsi);

  for (const node of graph.nodes) {
    if (!isIndicatorBlock(node.type)) continue;
    if ((node.type === "EMA" && emaNodes.slice(0, 2).includes(node)) || (node.type === "RSI" && rsiNodes[0] === node)) {
      continue;
    }
    const indicatorId = safeIndicatorId(node.id, node.type, indicators);
    indicators[indicatorId] = indicatorFromNode(node, { type: node.type, input: "close", period: defaultPeriod(node.type) });
  }

  return indicators;
}

function cloneDefaultIndicators(): Record<string, IndicatorSpec> {
  return Object.fromEntries(
    Object.entries(DEFAULT_INDICATORS).map(([key, value]) => [key, { ...value }]),
  );
}

function indicatorNodes(graph: StrategyGraphState, type: IndicatorBlockType): StrategyGraphNode[] {
  return graph.nodes.filter((node) => node.type === type);
}

function indicatorFromNode(node: StrategyGraphNode, fallback: IndicatorSpec): IndicatorSpec {
  return {
    type: isIndicatorBlock(node.type) ? node.type : fallback.type,
    input: "close",
    period: positiveInteger(node.params.period, fallback.period),
  };
}

function indicatorEntries(value: unknown): Array<[string, IndicatorSpec]> {
  if (Array.isArray(value)) {
    return value
      .map((entry, index): [string, IndicatorSpec] | null => {
        if (!isIndicatorRecord(entry)) return null;
        const id = typeof entry.id === "string" ? entry.id : `node_${index + 1}`;
        return [id, normalizeIndicatorRecord(entry)];
      })
      .filter((entry): entry is [string, IndicatorSpec] => entry !== null);
  }
  if (!isRecord(value)) return [];
  return Object.entries(value)
    .map(([id, entry]): [string, IndicatorSpec] | null => {
      if (!isIndicatorRecord(entry)) return null;
      return [id, normalizeIndicatorRecord(entry)];
    })
    .filter((entry): entry is [string, IndicatorSpec] => entry !== null);
}

function normalizeIndicatorRecord(value: Record<string, unknown>): IndicatorSpec {
  const type = isIndicatorBlock(value.type) ? value.type : "EMA";
  return {
    type,
    input: "close",
    period: positiveInteger(value.period, defaultPeriod(type)),
  };
}

function defaultPeriod(type: IndicatorBlockType): number {
  return {
    EMA: 20,
    SMA: 20,
    RSI: 14,
    MACD: 12,
    ATR: 14,
    BollingerBands: 20,
    VWAP: 20,
  }[type];
}

function positiveInteger(value: unknown, fallback: number): number {
  const numeric = typeof value === "number" ? value : typeof value === "string" ? Number(value) : NaN;
  return Number.isInteger(numeric) && numeric > 0 ? numeric : fallback;
}

function safeIndicatorId(id: string, type: IndicatorBlockType, indicators: Record<string, IndicatorSpec>): string {
  const base = id && !id.startsWith("node_") ? id : `${type.toLowerCase()}_${Object.keys(indicators).length + 1}`;
  const normalized = base.replace(/[^A-Za-z0-9_]/g, "_").replace(/^([0-9])/, "indicator_$1");
  let candidate = normalized || `${type.toLowerCase()}_${Object.keys(indicators).length + 1}`;
  let suffix = 2;
  while (candidate in indicators) {
    candidate = `${normalized}_${suffix}`;
    suffix += 1;
  }
  return candidate;
}

function isIndicatorBlock(value: unknown): value is IndicatorBlockType {
  return INDICATOR_BLOCKS.includes(value as IndicatorBlockType);
}

function isIndicatorRecord(value: unknown): value is Record<string, unknown> {
  return isRecord(value) && isIndicatorBlock(value.type);
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}
