import { describe, expect, it } from "vitest";
import { addStrategyBlock, graphToStrategySpec, strategySpecToGraph, updateStrategyBlockParams } from "./strategySpec";

describe("strategy graph helpers", () => {
  it("adds canonical blocks and serializes them to a backend-valid draft StrategySpec shape", () => {
    let graph = addStrategyBlock({ nodes: [], edges: [] }, "EMA");
    graph = updateStrategyBlockParams(graph, graph.nodes[0].id, { period: 21 });

    const spec = graphToStrategySpec(graph);

    expect(graph.nodes[0].type).toBe("EMA");
    expect(spec).toMatchObject({
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
      indicators: {
        ema_fast: { type: "EMA", input: "close", period: 21 },
        ema_slow: { type: "EMA", input: "close", period: 50 },
        rsi: { type: "RSI", input: "close", period: 14 },
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
    });
  });

  it("round-trips canonical StrategySpec indicators back into editable graph nodes", () => {
    const spec = graphToStrategySpec({ nodes: [], edges: [] });
    const graph = strategySpecToGraph(spec);

    expect(graph.nodes.map((node) => node.type)).toEqual(["EMA", "EMA", "RSI"]);
    expect(graph.nodes[0]).toMatchObject({ id: "ema_fast", params: { period: 20 } });
  });

  it("updates node params without accepting unsupported block types", () => {
    const graph = addStrategyBlock({ nodes: [], edges: [] }, "RSI");
    const updated = updateStrategyBlockParams(graph, graph.nodes[0].id, { period: 14 });

    expect(updated.nodes[0].params.period).toBe(14);
    expect(() => addStrategyBlock({ nodes: [], edges: [] }, "submit_order")).toThrow("unsupported strategy block");
  });
});
