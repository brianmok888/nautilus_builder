import { validateBacktestProfile } from "../../lib/api";
import { AdapterSelector } from "./AdapterSelector";
import { DataAvailabilityPanel } from "./DataAvailabilityPanel";
import { InstrumentSearch } from "./InstrumentSearch";

const adapter_profile_id = "adapter_profile_pending_backend_validation";

export const MarketProfilePanel = () => {
  return (
    <section aria-label="market profile">
      <AdapterSelector />
      <InstrumentSearch />
      <DataAvailabilityPanel />
      <p>Profile identity: {adapter_profile_id}</p>
      <p>Validation action: {validateBacktestProfile.name}</p>
    </section>
  );
};
