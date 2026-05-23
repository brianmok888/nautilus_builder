import { MarketSelectionPanel } from "./MarketSelectionPanel";
import { StrategyBuilderCanvas } from "./StrategyBuilderCanvas";
import { StrategySpecEditor } from "./StrategySpecEditor";
import { fetchAdapters, fetchStrategies, validateBacktestProfile } from "../../lib/api";

const backendDataContracts = [fetchAdapters, fetchStrategies, validateBacktestProfile];

export const StrategyBuilderWorkspace = () => {
  return (
    <section>
      <MarketSelectionPanel />
      <StrategyBuilderCanvas />
      <StrategySpecEditor />
      <p>Backend data contracts connected: {backendDataContracts.length}</p>
      <p>All drafts require backend validation before any backtest request.</p>
    </section>
  );
};
