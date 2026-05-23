import { BlockInspector } from "./BlockInspector";
import { BlockPalette } from "./BlockPalette";
import { MarketSelectionPanel } from "./MarketSelectionPanel";
import { StrategyBuilderCanvas } from "./StrategyBuilderCanvas";
import { StrategyGraphCanvas } from "./StrategyGraphCanvas";
import { StrategySpecEditor } from "./StrategySpecEditor";
import { ValidationPanel } from "./ValidationPanel";
import { fetchAdapters, fetchStrategies, validateBacktestProfile } from "../../lib/api";
import { MarketProfilePanel } from "../market/MarketProfilePanel";

const backendDataContracts = [fetchAdapters, fetchStrategies, validateBacktestProfile];

export const StrategyBuilderWorkspace = () => {
  return (
    <section>
      <MarketSelectionPanel />
      <MarketProfilePanel />
      <BlockPalette />
      <StrategyBuilderCanvas />
      <StrategyGraphCanvas />
      <BlockInspector />
      <StrategySpecEditor />
      <ValidationPanel errors={[]} />
      <p>Backend data contracts connected: {backendDataContracts.length}</p>
      <p>All drafts require backend validation before any backtest request.</p>
    </section>
  );
};
