import { fetchStrategies } from "../../lib/api";

export default function StrategiesPage() {
  return (
    <main>
      <h1>Strategy list</h1>
      <p>Saved StrategySpec drafts and versions are backend-owned records.</p>
      <p>Data source: {fetchStrategies.name}</p>
    </main>
  );
}
