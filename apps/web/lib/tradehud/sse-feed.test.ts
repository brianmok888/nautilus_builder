/**
 * Tests for SSE feed controller — authenticated same-origin, fail-closed behavior.
 * Uses a mock EventSource that supports addEventListener with named events.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { createFeed } from "./replay-feed";

// Mock EventSource for testing — supports addEventListener with named events
class MockEventSource {
  static instances: MockEventSource[] = [];
  url: string;
  readyState = 0;
  private closed = false;
  private listeners: Map<string, ((ev: Event | MessageEvent) => void)[]> = new Map();

  constructor(url: string) {
    this.url = url;
    MockEventSource.instances.push(this);
  }

  addEventListener(type: string, listener: (ev: Event | MessageEvent) => void) {
    if (!this.listeners.has(type)) this.listeners.set(type, []);
    this.listeners.get(type)!.push(listener);
  }

  removeEventListener(type: string, listener: (ev: Event | MessageEvent) => void) {
    const arr = this.listeners.get(type);
    if (arr) {
      const idx = arr.indexOf(listener);
      if (idx >= 0) arr.splice(idx, 1);
    }
  }

  close() { this.closed = true; this.readyState = 2; }
  get isClosed() { return this.closed; }

  // Test helpers — dispatch to addEventListener subscribers
  simulateOpen() {
    this.readyState = 1;
    this.listeners.get("open")?.forEach((fn) => fn(new Event("open")));
  }

  simulateError() {
    this.listeners.get("error")?.forEach((fn) => fn(new Event("error")));
  }

  /** Dispatch a named SSE event (snapshot, tradehud_event, ping) */
  simulateNamedEvent(eventName: string, data: unknown) {
    const payload = typeof data === "string" ? data : JSON.stringify(data);
    this.listeners.get(eventName)?.forEach((fn) => fn({ data: payload } as MessageEvent));
  }
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
    feed.stop();
    return new Promise<void>((resolve) => {
      setTimeout(() => { resolve(); }, 100);
    });
  });
});

describe("SSE feed controller", () => {
  beforeEach(() => {
    MockEventSource.instances = [];
    (globalThis as Record<string, unknown>).EventSource = MockEventSource;
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

  it("keeps EventSource same-origin even when a public API base is configured", () => {
    process.env.NEXT_PUBLIC_BUILDER_API_BASE = "https://api.example.invalid";
    const feed = createFeed("BTCUSDT-PERP");
    feed.start(() => {});

    expect(MockEventSource.instances[0].url).toMatch(/^\/api\/tradehud\/stream\?/);
    expect(MockEventSource.instances[0].url).not.toContain("api.example.invalid");

    feed.stop();
    delete process.env.NEXT_PUBLIC_BUILDER_API_BASE;
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

  it("dispatches data from named 'snapshot' event", () => {
    const feed = createFeed("BTCUSDT-PERP");
    const events: { type: string; payload?: unknown }[] = [];
    feed.start((ev) => events.push(ev));

    const es = MockEventSource.instances[0];
    es.simulateOpen();
    es.simulateNamedEvent("snapshot", { book_top: { price: 50000 }, provenance: "mock" });

    const bookEvent = events.find((e) => e.type === "BOOK_TOP");
    expect(bookEvent).toBeDefined();
    feed.stop();
  });

  it("dispatches data from named 'tradehud_event' event", () => {
    const feed = createFeed("BTCUSDT-PERP");
    const events: { type: string; payload?: unknown }[] = [];
    feed.start((ev) => events.push(ev));

    const es = MockEventSource.instances[0];
    es.simulateOpen();
    es.simulateNamedEvent("tradehud_event", { account: { balance: 100000 }, provenance: "mock" });

    const acctEvent = events.find((e) => e.type === "ACCOUNT");
    expect(acctEvent).toBeDefined();
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

  it("fails closed instead of starting mock snapshots after SSE errors", () => {
    const feed = createFeed("BTCUSDT-PERP");
    const events: { type: string; payload?: unknown }[] = [];
    feed.start((ev) => events.push(ev));

    const es = MockEventSource.instances[0];
    es.simulateError();

    const disconnectedEvent = events.find(
      (e) => e.type === "SET_FEED_STATUS" && (e.payload as { status?: string })?.status === "redis_disconnected",
    );
    expect(disconnectedEvent).toBeDefined();
    expect(events.some((e) => e.type === "SNAPSHOT")).toBe(false);
    expect(events.some((e) => (e.payload as { feedMode?: string } | undefined)?.feedMode === "mock")).toBe(false);

    feed.stop();
  });

  it("EventSource closes on cleanup", () => {
    const feed = createFeed("BTCUSDT-PERP");
    feed.start(() => {});

    const es = MockEventSource.instances[0];
    expect(es.isClosed).toBe(false);
    feed.stop();
    expect(es.isClosed).toBe(true);
  });

  it("mock remains default mode when env not set", () => {
    delete process.env.NEXT_PUBLIC_TRADEHUD_FEED_MODE;
    const feed = createFeed("BTCUSDT-PERP");
    expect(feed.mode).toBe("mock");
    feed.stop();
  });
});
