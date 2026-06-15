/**
 * Time formatting for dense trade displays.
 */

export function fmtTime(ns: number | null | undefined): string {
  if (ns == null) return "—";
  const ms = Math.floor(ns / 1_000_000);
  const d = new Date(ms);
  const hh = String(d.getHours()).padStart(2, "0");
  const mm = String(d.getMinutes()).padStart(2, "0");
  const ss = String(d.getSeconds()).padStart(2, "0");
  const mmm = String(d.getMilliseconds()).padStart(3, "0");
  return `${hh}:${mm}:${ss}.${mmm}`;
}

export function fmtClock(ns: number | null | undefined): string {
  if (ns == null) return "—";
  const ms = Math.floor(ns / 1_000_000);
  const d = new Date(ms);
  return d.toLocaleTimeString("en-US", { hour12: false });
}

export function fmtLatency(us: number | null | undefined): string {
  if (us == null) return "—";
  if (us < 1_000) return Math.round(us) + "\u00b5s";
  if (us < 1_000_000) return (us / 1_000).toFixed(2) + "ms";
  return (us / 1_000_000).toFixed(2) + "s";
}
