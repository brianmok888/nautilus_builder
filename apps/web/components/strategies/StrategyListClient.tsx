"use client";

import { useEffect, useState } from "react";
import { createStrategy, fetchStrategies } from "../../lib/api";
import type { StrategySummary } from "../../lib/types";

const draftSpec = { schema_version: "1.0.0", version: "0.1.0-draft.1", stage: "draft", status: "draft" };

export function StrategyListClient() {
  const [strategies, setStrategies] = useState<StrategySummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchStrategies().then(setStrategies).catch(() => setError("Unable to load strategies."));
  }, []);

  async function handleCreateDraft() {
    setSaving(true);
    setError(null);
    try {
      const created = await createStrategy(draftSpec);
      setStrategies((current) => [
        ...(current ?? []),
        { strategy_id: created.strategy_id, strategy_lineage_id: created.strategy_lineage_id, latest_spec: created.spec },
      ]);
    } catch {
      setError("Unable to create draft.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <section>
      <button type="button" onClick={handleCreateDraft} disabled={saving}>{saving ? "Creating…" : "Create draft"}</button>
      {error ? <p role="alert">{error}</p> : null}
      {strategies === null ? <p>Loading strategies…</p> : null}
      {strategies?.length === 0 ? <p>No saved strategies yet.</p> : null}
      <ul>
        {strategies?.map((strategy) => (
          <li key={strategy.strategy_id}>
            <a href={`/strategies/${strategy.strategy_id}`}>{strategy.strategy_id}</a> <span>{strategy.strategy_lineage_id}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}
