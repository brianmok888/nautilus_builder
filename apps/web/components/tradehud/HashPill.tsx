"use client";

export function HashPill({ hash, label }: { hash: string; label?: string }) {
  if (!hash) return <span className="tradehud-muted">—</span>;
  const short = hash.length > 16 ? hash.slice(0, 8) + "…" + hash.slice(-6) : hash;
  return (
    <span className="tradehud-hash-pill" title={hash}>
      {label ? `${label}:` : ""}{short}
    </span>
  );
}
