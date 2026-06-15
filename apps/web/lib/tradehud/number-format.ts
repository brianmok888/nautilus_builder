/**
 * Compact number formatting for dense operator displays.
 */

export function fmtPrice(n: number | null | undefined, decimals = 2): string {
  if (n == null || !isFinite(n)) return "—";
  return n.toLocaleString("en-US", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

export function fmtQty(n: number | null | undefined, decimals = 4): string {
  if (n == null || !isFinite(n)) return "—";
  if (Math.abs(n) >= 1_000_000) return (n / 1_000_000).toFixed(2) + "M";
  if (Math.abs(n) >= 1_000) return (n / 1_000).toFixed(2) + "K";
  return n.toFixed(decimals);
}

export function fmtNotional(n: number | null | undefined): string {
  if (n == null || !isFinite(n)) return "—";
  if (Math.abs(n) >= 1_000_000) return "$" + (n / 1_000_000).toFixed(2) + "M";
  if (Math.abs(n) >= 1_000) return "$" + (n / 1_000).toFixed(1) + "K";
  return "$" + n.toFixed(2);
}

export function fmtBps(n: number | null | undefined): string {
  if (n == null || !isFinite(n)) return "—";
  return n.toFixed(1) + " bps";
}

export function fmtPct(n: number | null | undefined): string {
  if (n == null || !isFinite(n)) return "—";
  return (n * 100).toFixed(2) + "%";
}

export function fmtSigned(n: number | null | undefined, decimals = 2): string {
  if (n == null || !isFinite(n)) return "—";
  const s = n.toFixed(decimals);
  return n >= 0 ? "+" + s : s;
}

export function fmtAge(ms: number | null | undefined): string {
  if (ms == null) return "—";
  if (ms < 1_000) return Math.round(ms) + "ms";
  if (ms < 60_000) return (ms / 1_000).toFixed(1) + "s";
  return Math.floor(ms / 60_000) + "m";
}
