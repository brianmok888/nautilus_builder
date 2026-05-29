"use client";

import Link from "next/link";

import { useEffect, useState } from "react";
import { createStrategy, fetchStrategies } from "../../lib/api";
import type { StrategySummary } from "../../lib/types";

const draftSpec = {
  schema_version: "1.0.0",
  version: "0.1.0-draft.1",
  stage: "draft",
  status: "draft",
  created_from: "user",
  is_frozen: false,
  adapter_id: "BINANCE_PERP",
  venue: "BINANCE",
  instrument_id: "BTCUSDT-PERP",
  bar_type: "BTCUSDT-PERP.BINANCE-5-MINUTE-LAST-EXTERNAL",
  data_range: { start: "2025-01-01T00:00:00Z", end: "2025-06-01T00:00:00Z" },
  indicators: {
    ema_fast: { type: "EMA", input: "close", period: 20 },
    ema_slow: { type: "EMA", input: "close", period: 50 },
    rsi: { type: "RSI", input: "close", period: 14 },
  },
  rules: {
    long_entry: {
      all: [{ crossed_above: ["ema_fast", "ema_slow"] }, { gt: ["rsi", 52] }],
    },
    long_exit: {
      any: [{ crossed_below: ["ema_fast", "ema_slow"] }, { lt: ["rsi", 45] }],
    },
  },
  risk: {
    position_size_pct: 0.05,
    stop_loss_pct: 0.012,
    take_profit_pct: 0.024,
    max_hold_bars: 48,
  },
  validation: {
    bar_close_only: true,
    no_lookahead_required: true,
    requires_backtest_before_shadow: true,
    output_mode: "signal_preview_only",
  },
  provenance: { created_by: "user", parent_version_id: null },
};

export function StrategyListClient() {
  const [strategies, setStrategies] = useState<StrategySummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchStrategies()
      .then(setStrategies)
      .catch(() => setError("Unable to load strategies."));
  }, []);

  async function handleCreateDraft() {
    setSaving(true);
    setError(null);
    try {
      const created = await createStrategy(draftSpec);
      setStrategies((current) => [
        ...(current ?? []),
        {
          strategy_id: created.strategy_id,
          strategy_lineage_id: created.strategy_lineage_id,
          latest_spec: created.spec,
          status: created.status,
        },
      ]);
    } catch {
      setError("Unable to create draft.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="card list-card">
      <button type="button" onClick={handleCreateDraft} disabled={saving}>
        {saving ? "Creating…" : "Create draft"}
      </button>
      {error ? (
        <p className="alert" role="alert">
          {error}
        </p>
      ) : null}
      {strategies === null ? <p>Loading strategies…</p> : null}
      {strategies?.length === 0 ? <p>No saved strategies yet.</p> : null}
      <ul>
        {strategies?.map((strategy) => (
          <li key={strategy.strategy_id}>
            <Link href={`/strategies/${strategy.strategy_id}`}>
              {strategy.strategy_id}
            </Link>{" "}
            <span>{strategy.strategy_lineage_id}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}
