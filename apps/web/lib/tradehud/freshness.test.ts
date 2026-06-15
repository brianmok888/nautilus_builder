import { describe, it, expect } from "vitest";
import { computeFreshness, statusFromFreshness } from "./freshness";

describe("Freshness utilities", () => {
  it("marks missing data as missing, NOT true_zero", () => {
    const result = computeFreshness({
      last_update_ts_ns: null,
      receive_ts_ns: null,
      true_zero: false,
    });
    expect(result.missing).toBe(true);
    expect(result.true_zero).toBe(false);
    expect(result.source_status).toBe("missing");
  });

  it("marks true_zero distinctly from missing", () => {
    const result = computeFreshness({
      last_update_ts_ns: 1_000_000_000n,
      receive_ts_ns: 1_000_000_000n,
      true_zero: true,
    });
    expect(result.true_zero).toBe(true);
    expect(result.missing).toBe(false);
    expect(result.source_status).toBe("true_zero");
  });

  it("marks stale data correctly", () => {
    const now = BigInt(Date.now()) * 1_000_000n;
    const oldTs = now - 10_000_000_000n; // 10s ago
    const result = computeFreshness({
      last_update_ts_ns: oldTs,
      receive_ts_ns: oldTs,
      true_zero: false,
      now_ns: now,
    });
    expect(result.stale).toBe(true);
    expect(result.missing).toBe(false);
    expect(result.source_status).toBe("stale");
  });

  it("marks live data correctly", () => {
    const now = BigInt(Date.now()) * 1_000_000n;
    const recentTs = now - 500_000_000n; // 0.5s ago
    const result = computeFreshness({
      last_update_ts_ns: recentTs,
      receive_ts_ns: recentTs,
      true_zero: false,
      now_ns: now,
    });
    expect(result.stale).toBe(false);
    expect(result.missing).toBe(false);
    expect(result.source_status).toBe("live");
  });
});
