/**
 * Freshness calculation utilities.
 * Never treat missing as zero. Distinguish true_zero from missing.
 */
import type { SourceFreshnessMeta, SourceStatus } from "./types";

const NOW = (): number => Date.now() * 1_000_000; // ns

const STALE_THRESHOLD_MS = 5_000;

export function computeAge(
  lastUpdateNs: number | null,
  receiveNs?: number | null,
): number | null {
  if (lastUpdateNs == null) return null;
  const ref = receiveNs ?? NOW();
  return Math.max(0, Math.round((ref - lastUpdateNs) / 1_000_000));
}

export function isStale(ageMs: number | null): boolean {
  if (ageMs == null) return true;
  return ageMs > STALE_THRESHOLD_MS;
}

export function buildFreshness(
  lastUpdateNs: number | null,
  provenance: string,
  opts?: {
    trueZero?: boolean;
    unavailable?: boolean;
    receiveNs?: number | null;
  },
): SourceFreshnessMeta {
  const trueZero = opts?.trueZero ?? false;
  const unavailable = opts?.unavailable ?? false;
  const receiveNs = opts?.receiveNs ?? NOW();
  const ageMs = computeAge(lastUpdateNs, receiveNs);
  const stale = !unavailable && !trueZero && isStale(ageMs);
  const missing = lastUpdateNs == null && !trueZero;

  let status: SourceStatus;
  if (unavailable) status = "unavailable";
  else if (missing) status = "missing";
  else if (trueZero) status = "true_zero";
  else if (stale) status = "stale";
  else if (provenance === "mock" || provenance === "synthetic") status = "synthetic";
  else status = "live";

  return {
    source_available: !unavailable && !missing,
    last_update_ts_ns: lastUpdateNs,
    receive_ts_ns: receiveNs,
    age_ms: ageMs,
    stale,
    missing,
    true_zero,
    provenance,
    source_status: status,
  };
}

export function syntheticFreshness(
  lastUpdateNs: number | null,
  provenance: string = "mock",
): SourceFreshnessMeta {
  return buildFreshness(lastUpdateNs, provenance);
}
