import Link from "next/link";
export default function BacktestsPage() {
  return (
    <main className="app-shell">
      <h1>Backtest Center</h1>
      <p>Select a backtest job from the dashboard or create a new run.</p>
      <nav>
        <Link href="/">← Back to Strategy Builder</Link>
      </nav>
    </main>
  );
}
