# TradeHUD SSE Gateway V1

## Scope

This branch adds a **read-only** Server-Sent Events (SSE) transport layer for the Web TradeHUD.

- ✅ Synthetic/mock runtime event stream by default
- ✅ Initial snapshot event on connection
- ✅ Periodic mock event updates (1.5s interval)
- ✅ Keep-alive pings (15s interval)
- ✅ Frontend auto-reconnect with bounded exponential backoff
- ✅ Frontend fallback to local mock mode when backend unavailable
- ✅ No direct browser Redis/PostgreSQL access
- ✅ No exchange credentials in browser
- ✅ No order authority

> ⚠️ **This SSE gateway is NOT production Nautilus-Daedalus live Redis integration yet.**
> It is transport and UI integration layer using synthetic/mock events by default.
> Real ND Redis stream consumption must be implemented in a later isolated branch.

## Architecture Boundary

### Correct V1 Flow (this branch)

```
Synthetic/mock TradeHUD event generator
  → Builder API SSE route (GET /api/tradehud/stream)
  → Browser EventSource client
  → TradeHUD reducer
  → TradeHUD UI
```

### Future Flow (not in this branch)

```
Nautilus-Daedalus runtime
  → Redis Streams
  → Builder API runtime stream adapter
  → Builder API SSE route
  → Browser TradeHUD
```

### Forbidden Flow

- Browser → Redis directly ❌
- Browser → PostgreSQL directly ❌
- Browser → Exchange adapter directly ❌
- Browser → `submit_order()` ❌
- Browser → create `TradeAction` ❌
- Browser → approve `GateDecision` ❌
- Browser → hold exchange credentials ❌

**Only `run_execution_lane` may call `submit_order()`.**
The Web TradeHUD must only display runtime evidence.

## SSE Endpoint

### `GET /api/tradehud/stream`

Returns `text/event-stream` with standard SSE named-event framing:

```
event: snapshot
data: {"provenance": "mock", "source_status": "synthetic", "book_top": {...}, ...}

event: tradehud_event
data: {"provenance": "mock", "source_status": "synthetic", "tick": 1, ...}

event: ping
data: {"server_time": 1234567890, "provenance": "mock", "source_status": "synthetic"}
```

- **Initial snapshot**: Full TradeHUD state burst on connect
- **Periodic events**: `tradehud_event` every 1500ms
- **Keep-alive**: `ping` every 15s
- **Provenance**: All events carry `provenance: "mock"` and `source_status: "synthetic"`
- **Disconnect**: Generator unwinds cleanly via anyio cancellation — no leaked tasks

## Environment Variables

| Variable | Values | Default |
|----------|--------|---------|
| `NEXT_PUBLIC_TRADEHUD_FEED_MODE` | `mock` \| `snapshot` \| `sse` | `mock` |
| `NEXT_PUBLIC_BUILDER_API_BASE` | API base URL | `http://127.0.0.1:8000` |

**Default must remain `mock`** — safe without any backend.

## Frontend Behavior

### Mock Mode (default)
- Deterministic local synthetic events only
- No backend required
- Badge: `LOCAL MOCK`

### Snapshot Mode
- Fetches `GET /api/tradehud/snapshot` every 2s
- Falls back to mock if unavailable
- Badge: `SNAPSHOT API`

### SSE Mode
- Connects via `EventSource` to `/api/tradehud/stream`
- Named event listeners: `snapshot`, `tradehud_event`, `ping`
- Bounded exponential backoff: 500ms initial → 15s max, with ±10% jitter
- Max 5 reconnect attempts → auto-fallback to mock
- Badge: `SSE SYNTHETIC` (live), `SSE RECONNECTING`, `SSE FALLBACK → MOCK`

## UI Safety Labels

The TradeHUD always displays:
- `⚠ NO BROWSER ORDER AUTHORITY`
- Feed mode: `MOCK` / `SNAPSHOT` / `SSE`
- Feed status badge with provenance
- Synthetic/mock data is always visibly synthetic

## Local Demo Server

`sse_demo_server.py` is a **LOCAL DEVELOPMENT ONLY** standalone server for previewing
the SSE stream without running the full Builder API. It:
- Uses permissive CORS (wildcard) for local dev
- Provides no authentication or authorization
- Is NOT imported by production FastAPI app
- Must NOT be referenced from production Dockerfiles or deployment scripts

## Files

| File | Purpose |
|------|---------|
| `services/api/routes/tradehud_sse.py` | SSE event generator + StreamingResponse builder |
| `services/api/sse_demo_server.py` | Local-only standalone demo server |
| `apps/web/lib/tradehud/replay-feed.ts` | Feed controller (mock/snapshot/sse modes) |
| `apps/web/lib/tradehud/types.ts` | TradeHudState with feedMode/feedStatus |
| `apps/web/lib/tradehud/reducer.ts` | Central reducer handling all event types |
| `apps/web/components/tradehud/TradeHudTopBar.tsx` | Feed status display |
| `tests/web/test_tradehud_sse.py` | Backend SSE tests |
| `apps/web/lib/tradehud/sse-feed.test.ts` | Frontend SSE feed tests |
| `apps/web/lib/tradehud/safety-grep.test.ts` | Safety grep covering SSE files |

## What This Branch Adds

- Read-only SSE route (`GET /api/tradehud/stream`)
- Synthetic snapshot and event stream with standard named-event framing
- EventSource frontend client with named event listeners
- Reconnect/backoff/fallback behavior
- Feed status display in TradeHudTopBar
- Backend + frontend tests
- Safety grep coverage for SSE files
- Local-only demo server

## What This Branch Does NOT Add

- Real Redis stream adapter
- Production live ND runtime feed
- Exchange execution controls
- Browser credentials
- Order authority

## Next Recommended Branch

`feature/tradehud-redis-stream-adapter` — implement real Nautilus-Daedalus Redis Stream consumption as a separate adapter that feeds into the same SSE route.
