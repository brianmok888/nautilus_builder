import { ALLOWED_STRATEGY_BLOCKS } from "../../lib/strategySpec";

export const BlockPalette = () => {
  return (
    <aside aria-label="block palette">
      <h3>Blocks</h3>
      <ul>{ALLOWED_STRATEGY_BLOCKS.map((block) => <li key={block}>{block}</li>)}</ul>
    </aside>
  );
};
