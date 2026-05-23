import { ALLOWED_STRATEGY_BLOCKS } from "../../lib/strategySpec";

export const BlockPalette = ({ onAddBlock }: { onAddBlock?: (block: string) => void }) => {
  return (
    <aside aria-label="block palette">
      <h3>Blocks</h3>
      <ul>
        {ALLOWED_STRATEGY_BLOCKS.map((block) => (
          <li key={block}>
            <button type="button" onClick={() => onAddBlock?.(block)}>
              Add {block}
            </button>
          </li>
        ))}
      </ul>
    </aside>
  );
};
