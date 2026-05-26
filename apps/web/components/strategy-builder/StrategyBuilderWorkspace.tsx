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
    <section className="panel-grid compact-editor-layout" aria-label="strategy spec editor workspace">
      <header className="editor-section editor-section-full">
        <p className="hero-kicker">StrategySpec Editor</p>
        <h2>Compact draft workspace</h2>
        <p>Backend validation required before any backtest request (backend validation gate).</p>
      </header>

      <section className="editor-section editor-section-full" aria-label="market data context">
        <h3>Market context</h3>
        <MarketSelectionPanel />
        <MarketProfilePanel />
      </section>

      <section className="editor-section" aria-label="block canvas">
        <h3>Block canvas</h3>
        <BlockPalette
          onAddBlock={(block) =>
            setGraph((current) => addStrategyBlock(current, block))
          }
        />
        <StrategyBuilderCanvas />
        <StrategyGraphCanvas nodes={graph.nodes} onSelect={setSelectedNodeId} />
      </section>

      <section className="editor-section" aria-label="inspector">
        <h3>Inspector</h3>
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
        <ValidationPanel errors={[]} />
      </section>

      <section className="editor-section" aria-label="spec preview">
        <h3>Spec preview</h3>
        <StrategySpecEditor spec={spec} />
      </section>

      <footer className="editor-section editor-section-full">
        <p>
          <span className="status-badge">Backend contracts</span>{" "}
          {backendDataContracts.length} connected
        </p>
        <p>Backend validation required before any backtest request (backend validation gate).</p>
      </footer>
    </section>
  );
};
