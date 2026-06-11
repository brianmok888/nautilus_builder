"use client";

import { useEffect, useState } from "react";

export interface HealthStatus {
  status: "healthy" | "degraded" | "down";
  latencyMs: number | null;
  error: string | null;
}

export function useHealthCheck(intervalMs = 30000): HealthStatus {
  const [health, setHealth] = useState<HealthStatus>({
    status: "down",
    latencyMs: null,
    error: null,
  });

  useEffect(() => {
    let mounted = true;

    async function check() {
      const start = performance.now();
      try {
        // /health is a public unauthenticated endpoint; direct fetch is intentional.
        const response = await fetch("/health");
        const elapsed = performance.now() - start;
        if (!mounted) return;
        if (response.ok) {
          setHealth({ status: "healthy", latencyMs: Math.round(elapsed), error: null });
        } else {
          setHealth({ status: "degraded", latencyMs: Math.round(elapsed), error: `HTTP ${response.status}` });
        }
      } catch (err) {
        if (!mounted) return;
        setHealth({ status: "down", latencyMs: null, error: err instanceof Error ? err.message : "unreachable" });
      }
    }

    check();
    const id = setInterval(check, intervalMs);
    return () => {
      mounted = false;
      clearInterval(id);
    };
  }, [intervalMs]);

  return health;
}
