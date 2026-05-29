"use client";

import { useSearchParams } from "next/navigation";
import { BuilderDashboard } from "../components/dashboard/BuilderDashboard";

export default function HomePage() {
  const params = useSearchParams();
  const tab = params.get("tab") ?? "strategy";
  return (
    <main className="app-shell">
      <BuilderDashboard initialTab={tab} />
    </main>
  );
}
