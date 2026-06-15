import { describe, it, expect } from "vitest";
import { buildFreshness, computeAge, isStale, syntheticFreshness } from "./freshness";

describe("Freshness utilities", () => {
  it("marks missing data as missing, NOT true_zero", () => {
    const result = buildFreshness(null, "mock");
    expect(result.missing).toBe(true);
    expect(result.true_zero).toBe(false);
    expect(result.source_status).toBe("missing");
  });

  it("marks true_zero distinctly from missing", () => {
    const result = buildFreshness(Date.now() * 1_000_000, "mock", { trueZero: true });
    expect(result.true_zero).toBe(true);
    expect(result.missing).toBe(false);
    expect(result.source_status).toBe("true_zero");
  });

  it("marks stale data correctly", () => {
    const now = Date.now() * 1_000_000;
    const oldTs = now - 10_000_000_000; // 10s ago
    const result = buildFreshness(oldTs, "live", { receiveNs: now });
    expect(result.stale).toBe(true);
    expect(result.missing).toBe(false);
    expect(result.source_status).toBe("stale");
  });

  it("marks synthetic data correctly", () => {
    const now = Date.now() * 1_000_000;
    const recentTs = now - 500_000_000; // 0.5s ago
    const result = buildFreshness(recentTs, "mock", { receiveNs: now });
    expect(result.stale).toBe(false);
    expect(result.missing).toBe(false);
    expect(result.source_status).toBe("synthetic");
  });

  it("syntheticFreshness shortcut works", () => {
    const result = syntheticFreshness(Date.now() * 1_000_000);
    expect(result.provenance).toBe("mock");
    expect(result.source_available).toBe(true);
  });

  it("computeAge returns null for null input", () => {
    expect(computeAge(null)).toBeNull();
  });

  it("isStale returns true for null age", () => {
    expect(isStale(null)).toBe(true);
    expect(isStale(6000)).toBe(true);
    expect(isStale(1000)).toBe(false);
  });
});
