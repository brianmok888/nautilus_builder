"use client";

import Link from "next/link";

import { useEffect, useState } from "react";
import { fetchStrategyDetail } from "../../lib/api";
import type { StrategyDetail } from "../../lib/types";

export function StrategyDetailClient({ strategyId }: { strategyId: string }) {
  const [detail, setDetail] = useState<StrategyDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchStrategyDetail(strategyId)
      .then(setDetail)
      .catch(() => setError("Unable to load strategy detail."));
  }, [strategyId]);

  if (error)
    return (
      <p className="alert" role="alert">
        {error}
      </p>
    );
  if (!detail) return <p>Loading strategy detail…</p>;

  return (
    <section className="card list-card">
      <p>{detail.strategy_lineage_id}</p>
      <h2>Version history</h2>
      <ul>
        {detail.versions.map((version) => (
          <li key={version.strategy_version_id}>
            {version.strategy_version_id}
          </li>
        ))}
      </ul>
      <Link href={`/builder/${strategyId}`}>Open in Builder</Link>
    </section>
  );
}
