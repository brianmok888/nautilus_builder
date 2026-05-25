"use client";

import { useMemo, useState } from "react";
import { BlockInspector } from "./BlockInspector";
import { BlockPalette } from "./BlockPalette";
import { MarketSelectionPanel } from "./MarketSelectionPanel";
import { StrategyBuilderCanvas } from "./StrategyBuilderCanvas";
import { StrategyGraphCanvas } from "./StrategyGraphCanvas";
import { StrategySpecEditor } from "./StrategySpecEditor";
import { ValidationPanel } from "./ValidationPanel";
import {
  fetchAdapters,
  fetchStrategies,
  validateBacktestProfile,
} from "../../lib/api";
import {
  addStrategyBlock,
  graphToStrategySpec,
  updateStrategyBlockParams,
  type StrategyGraphState,
} from "../../lib/strategySpec";
import { MarketProfilePanel } from "../market/MarketProfilePanel";

const backendDataContracts = [
  fetchAdapters,
  fetchStrategies,
  validateBacktestProfile,
];

export const StrategyBuilderWorkspace = () => {
  const [graph, setGraph] = useState<StrategyGraphState>({
    nodes: [],
    edges: [],
  });
  const [selectedNodeId, setSelectedNodeId] = useState<string | undefined>();
  const selectedNode = graph.nodes.find((node) => node.id === selectedNodeId);
  const spec = useMemo(() => graphToStrategySpec(graph), [graph]);

  return (
    <section className="panel-grid">
      <MarketSelectionPanel />
      <MarketProfilePanel />
      <BlockPalette
        onAddBlock={(block) =>
          setGraph((current) => addStrategyBlock(current, block))
        }
      />
      <StrategyBuilderCanvas />
      <StrategyGraphCanvas nodes={graph.nodes} onSelect={setSelectedNodeId} />
      <BlockInspector
        selectedNode={selectedNode}
        onChangeParams={(params) => {
          if (selectedNode) {
            setGraph((current) =>
              updateStrategyBlockParams(current, selectedNode.id, params),
            );
          }
        }}
      />
      <StrategySpecEditor spec={spec} />
      <ValidationPanel errors={[]} />
      <p>
        <span className="status-badge">Backend contracts</span>{" "}
        {backendDataContracts.length} connected
      </p>
      <p>All drafts require backend validation before any backtest request.</p>
    </section>
  );
};
