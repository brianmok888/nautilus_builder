import { MarketSelectionPanel } from "./MarketSelectionPanel";
import { StrategyBuilderCanvas } from "./StrategyBuilderCanvas";
import { StrategySpecEditor } from "./StrategySpecEditor";

export const StrategyBuilderWorkspace = () => {
  return (
    <section>
      <MarketSelectionPanel />
      <StrategyBuilderCanvas />
      <StrategySpecEditor />
      <p>All drafts require backend validation before any backtest request.</p>
    </section>
  );
};
