# AGENTS — apps/web/lib/tradehud

TypeScript runtime for the TradeHUD observational monitor. Consumes normalized ND payloads; never owns runtime authority.

## Scope
- `types.ts` — TS interfaces mirroring `packages/tradehud_contracts/models.py` (book top/L2, trades, bars, liquidations, signals, gate, account/positions/orders, quant levels, lane + runtime health, `SourceStatus`, `SourceFreshnessMeta`).
- `reducer.ts` — pure `reducer(state, event)` over `TradeHudEvent`; `createInitialState()`. Owns bounded arrays via `pushBounded`.
- `selectors.ts` — derived views: `selectOrderBookTopN`, `selectRecentTrades`, `selectLanes`, `selectPriceRange`.
- `replay-feed.ts` — `createFeed(symbol)` factory; `FeedMode = "mock" | "snapshot" | "sse"` selected from env. Returns a `FeedController`.
- `sse-feed.ts`, `mock-feed.ts` — feed implementations (SSE EventSource; deterministic `MockFeed` with `SeededRng`).
- `freshness.ts` — `computeAge`, `isStale`, `buildFreshness` (status badge logic).
- `heatmap-buffer.ts`, `ring-buffer.ts` — bounded buffers for the bookmap heatmap and rolling windows.
- `number-format.ts`, `time-format.ts` — pure formatters (price/qty/notional/bps/pct/age; ns time/latency).
- `*.test.ts` — Vitest unit tests colocated with their module.

## Conventions
- `types.ts` is the TS mirror of the Python models — keep both in lockstep when the Python contract changes.
- `reducer` must stay pure: same `(state, event)` → same output. No fetch, no side effects.
- Feeds dispatch `TradeHudEvent`s into the reducer; components subscribe via selectors, never call feeds directly.
- Formatters in `number-format.ts`/`time-format.ts` accept `null` and render a safe placeholder.

## Anti-patterns (THIS PROJECT)
- Never let this layer place orders, call `submit_order`, or import execution-lane internals.
- Never invent TS types that drift from `packages/tradehud_contracts/models.py`.
- Never import antd or React here — this is a pure logic layer consumed by `components/tradehud/`.
- Never add `fetch` outside the feed modules; `sse-feed.ts`/`replay-feed.ts` are the only network entry points.

## Verification
```bash
cd apps/web && npx vitest run lib/tradehud
```
