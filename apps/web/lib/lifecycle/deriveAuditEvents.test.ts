import { describe, it, expect } from "vitest";
import { deriveAuditEvents } from "./deriveAuditEvents";
import type { AuditInput } from "./deriveAuditEvents";

describe("deriveAuditEvents", () => {
  const baseInput = (overrides: Partial<AuditInput> = {}): AuditInput => ({
    strategyId: "test-001",
    ...overrides,
  });

  it("renders at least a created event even with minimal data", () => {
    const events = deriveAuditEvents(baseInput());
    expect(events.length).toBeGreaterThanOrEqual(1);
    expect(events[0].kind).toBe("created");
    expect(events[0].status).toBe("info");
  });

  it("includes validated event when validation passes", () => {
    const events = deriveAuditEvents(
      baseInput({ validation: { bar_close_only: true, no_lookahead: true } }),
    );
    const validated = events.find((e) => e.kind === "validated");
    expect(validated).toBeDefined();
    expect(validated!.status).toBe("success");
  });

  it("includes validation_failed event when validation has false fields", () => {
    const events = deriveAuditEvents(
      baseInput({ validation: { bar_close_only: false } }),
    );
    const failed = events.find((e) => e.kind === "validation_failed");
    expect(failed).toBeDefined();
    expect(failed!.status).toBe("error");
  });

  it("includes compiled event when compile hash exists", () => {
    const events = deriveAuditEvents(
      baseInput({ compileHash: "a".repeat(64) }),
    );
    const compiled = events.find((e) => e.kind === "compiled");
    expect(compiled).toBeDefined();
    expect(compiled!.status).toBe("success");
  });

  it("includes replay_completed when backtest succeeded", () => {
    const events = deriveAuditEvents(
      baseInput({
        backtestJobId: "job-1",
        backtestJobStatus: "succeeded",
      }),
    );
    const replay = events.find((e) => e.kind === "replay_completed");
    expect(replay).toBeDefined();
    expect(replay!.status).toBe("success");
  });

  it("includes replay_failed when backtest failed", () => {
    const events = deriveAuditEvents(
      baseInput({
        backtestJobId: "job-1",
        backtestJobStatus: "failed",
      }),
    );
    const replay = events.find((e) => e.kind === "replay_failed");
    expect(replay).toBeDefined();
    expect(replay!.status).toBe("error");
  });

  it("includes promotion_ready when status is approved", () => {
    const events = deriveAuditEvents(
      baseInput({ status: "approved" }),
    );
    const promo = events.find((e) => e.kind === "promotion_ready");
    expect(promo).toBeDefined();
    expect(promo!.status).toBe("success");
  });

  it("includes promotion_requested when promotionRequested is true", () => {
    const events = deriveAuditEvents(
      baseInput({ promotionRequested: true }),
    );
    const promo = events.find((e) => e.kind === "promotion_requested");
    expect(promo).toBeDefined();
    expect(promo!.status).toBe("info");
  });

  it("does not invent events for missing data", () => {
    const events = deriveAuditEvents(baseInput());
    // Only the "created" event should exist — no validation, compile, replay, promotion
    expect(events).toHaveLength(1);
    expect(events[0].kind).toBe("created");
  });

  it("includes createdBy in created event when available", () => {
    const events = deriveAuditEvents(
      baseInput({ createdBy: "user" }),
    );
    expect(events[0].actor).toBe("user");
    expect(events[0].detail).toContain("user");
  });
});
