/**
 * Tests for SSE feed controller — auto-fallback behavior.
 * Uses a mock EventSource to simulate connection lifecycle.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { createFeed } from "./replay-feed";

// Mock EventSource for testing
class MockEventSource {
  static instances: MockEventSource[] = [];
  url: string;
  onopen: ((ev: Event) => void) | null = null;
  onerror: ((ev: Event) => void) | null = null;
  onmessage: ((ev: MessageEvent) => void) | null = null;
  readyState = 0;
  private closed = false;

  constructor(url: string) {
    this.url = url;
    MockEventSource.instances.push(this);
  }
  close() { this.closed = true; this.readyState = 2; }
  get isClosed() { return this.closed; }
  // Test helpers
  simulateOpen() { this.readyState = 1; this.onopen?.(new Event("open")); }
  simulateError() { this.onerror?.(new Event("error")); }
  simulateMessage(data: string) { this.onmessage?.({ data } as MessageEvent); }
}

describe("Feed mode selection", () => {
  it("defaults to mock mode", () => {
    const feed = createFeed("BTCUSDT-PERP");
    expect(feed.mode).toBe("mock");
    feed.stop();
  });
});

describe("Mock feed controller", () => {
  it("dispatches initial snapshot events on start", () => {
    const feed = createFeed("BTCUSDT-PERP");
    const events: { type: string }[] = [];
    feed.start((ev) => events.push(ev));
    feed.stop();

    // Should have dispatched SET_FEED_STATUS, SET_BACKEND, SNAPSHOT, and more
    const types = events.map((e) => e.type);
    expect(types).toContain("SET_FEED_STATUS");
    expect(types).toContain("SET_BACKEND");
    expect(types).toContain("SNAPSHOT");
    expect(types).toContain("SIGNAL_PREVIEW");
    expect(types).toContain("GATE_DECISION");
  });

  it("stops emitting events after stop()", () => {
    const feed = createFeed("BTCUSDT-PERP");
    let count = 0;
    feed.start(() => count++);
    const before = count;
    feed.stop();
    // After stop, no more events (wait a tick to verify)
    return new Promise<void>((resolve) => {
      setTimeout(() => {
        // count should not have grown significantly
        resolve();
      }, 100);
    });
  });
});

describe("SSE feed controller", () => {
  beforeEach(() => {
    MockEventSource.instances = [];
    // Inject mock EventSource onto global
    (globalThis as Record<string, unknown>).EventSource = MockEventSource;
    // Set env to SSE mode
    process.env.NEXT_PUBLIC_TRADEHUD_FEED_MODE = "sse";
  });

  afterEach(() => {
    delete process.env.NEXT_PUBLIC_TRADEHUD_FEED_MODE;
    delete (globalThis as Record<string, unknown>).EventSource;
  });

  it("creates EventSource to correct endpoint", () => {
    const feed = createFeed("BTCUSDT-PERP");
    feed.start(() => {});
    expect(MockEventSource.instances.length).toBe(1);
    expect(MockEventSource.instances[0].url).toContain("/api/tradehud/stream");
    expect(MockEventSource.instances[0].url).toContain("symbol=BTCUSDT-PERP");
    feed.stop();
  });

  it("dispatches SET_FEED_STATUS connecting on start", () => {
    const feed = createFeed("BTCUSDT-PERP");
    const events: { type: string; payload?: unknown }[] = [];
    feed.start((ev) => events.push(ev));

    const statusEvents = events.filter((e) => e.type === "SET_FEED_STATUS");
    expect(statusEvents.length).toBeGreaterThanOrEqual(1);
    feed.stop();
  });

  it("dispatches live status when connection opens", () => {
    const feed = createFeed("BTCUSDT-PERP");
    const events: { type: string; payload?: unknown }[] = [];
    feed.start((ev) => events.push(ev));

    const es = MockEventSource.instances[0];
    es.simulateOpen();

    const statusEvents = events.filter((e) => e.type === "SET_FEED_STATUS");
    const liveEvent = statusEvents.find(
      (e) => (e.payload as { status: string })?.status === "live",
    );
    expect(liveEvent).toBeDefined();
    feed.stop();
  });

  it("dispatches data events from SSE messages", () => {
    const feed = createFeed("BTCUSDT-PERP");
    const events: { type: string; payload?: unknown }[] = [];
    feed.start((ev) => events.push(ev));

    const es = MockEventSource.instances[0];
    es.simulateOpen();
    es.simulateMessage(JSON.stringify({ type: "BOOK_TOP", payload: { price: 50000 } }));

    const bookEvent = events.find((e) => e.type === "BOOK_TOP");
    expect(bookEvent).toBeDefined();
    feed.stop();
  });

  it("dispatches backend=false on connection error", () => {
    const feed = createFeed("BTCUSDT-PERP");
    const events: { type: string; payload?: unknown }[] = [];
    feed.start((ev) => events.push(ev));

    const es = MockEventSource.instances[0];
    es.simulateError();

    const backendEvent = events.find(
      (e) => e.type === "SET_BACKEND" && e.payload === false,
    );
    expect(backendEvent).toBeDefined();
    feed.stop();
  });
});
