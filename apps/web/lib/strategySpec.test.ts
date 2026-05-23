import { describe, expect, it } from "vitest";
import { addStrategyBlock, graphToStrategySpec, updateStrategyBlockParams } from "./strategySpec";

describe("strategy graph helpers", () => {
  it("adds canonical blocks and serializes them to draft StrategySpec", () => {
    const graph = addStrategyBlock({ nodes: [], edges: [] }, "EMA");

    expect(graph.nodes[0].type).toBe("EMA");
    expect(graphToStrategySpec(graph)).toMatchObject({ stage: "draft", status: "draft" });
  });

  it("updates node params without accepting unsupported block types", () => {
    const graph = addStrategyBlock({ nodes: [], edges: [] }, "RSI");
    const updated = updateStrategyBlockParams(graph, graph.nodes[0].id, { period: 14 });

    expect(updated.nodes[0].params.period).toBe(14);
    expect(() => addStrategyBlock({ nodes: [], edges: [] }, "submit_order")).toThrow("unsupported strategy block");
  });
});
