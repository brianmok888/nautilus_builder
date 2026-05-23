import { requestShadowPromotion } from "../../lib/api";

const strategy_version_id = "strategy_001_v002";
const result_id = "res_001";

export const PromotionRequestPanel = () => {
  return (
    <section aria-label="promotion request">
      <h3>Safe promotion request</h3>
      <p>Targets: shadow, signal-preview</p>
      <p>Requires manual approval before any downstream change.</p>
      <p>strategy_version_id: {strategy_version_id}</p>
      <p>result_id: {result_id}</p>
      <p>Contract: {requestShadowPromotion.name}</p>
    </section>
  );
};
