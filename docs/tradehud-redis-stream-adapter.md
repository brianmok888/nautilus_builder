# TradeHUD Redis Stream Adapter

## Overview

Read-only Redis Stream consumer that reads Nautilus-Daedalus (ND) runtime events from Redis Streams and feeds them into the TradeHUD SSE route.

**This adapter is purely observational.** It reads runtime evidence — it never writes to Redis, never submits orders, never creates TradeActions, and never exposes credentials.

## Architecture

```
Nautilus-Daedalus runtime
  → Redis Streams (XADD — runtime side)
  → RedisStreamAdapter (XREAD — read-only, Builder side)
  → SSE route (GET /api/tradehud/stream)
  → Browser EventSource client
  → TradeHUD UI
```

### Source Selection

| Condition | Source | Provenance | Source Status |
|-----------|--------|------------|---------------|
| REDIS_URL set + Redis reachable | Redis adapter | `redis` | `live` |
| REDIS_URL not set | Mock service | `mock` | `synthetic` |
| REDIS_URL set but Redis unreachable | Mock service (fallback) | `mock` | `synthetic` |

The SSE route automatically detects Redis availability at connection time and periodically retries if Redis comes back online.

## Redis Stream Convention

The adapter reads from streams prefixed with `nautilus:tradehud:`:

| Stream Key | Contract Model |
|------------|----------------|
| `nautilus:tradehud:book_top` | `MarketBookTopModel` |
| `nautilus:tradehud:book_l2` | `MarketBookL2Model` |
| `nautilus:tradehud:account` | `AccountSnapshotModel` |
| `nautilus:tradehud:positions` | `PositionSnapshotModel[]` |
| `nautilus:tradehud:open_orders` | `OpenOrderSnapshotModel[]` |
| `nautilus:tradehud:signal` | `StrategySignalPreviewModel` |
| `nautilus:tradehud:gate` | `GateDecisionModel` |
| `nautilus:tradehud:trade_action` | `TradeActionEvidenceModel` |
| `nautilus:tradehud:execution` | `ExecutionReportModel` |
| `nautilus:tradehud:quant_levels` | `QuantLevelsContextModel` |
| `nautilus:tradehud:tick_to_trade` | `TickToTradeTraceModel` |
| `nautilus:tradehud:runtime_health` | `RuntimeHealthModel` |

## Safety Boundaries

### ✅ Allowed
- `XREAD` — read stream entries (read-only)
- Parse stream entries into contract models
- Cache latest entry per stream
- Fall back to mock when Redis unavailable

### ❌ Forbidden
- `XADD` — never write to streams
- `SET` / `HSET` / `PUBLISH` — never write to Redis
- `DEL` — never delete from Redis
- `submit_order()` — never execute orders
- `create_trade_action()` — never create TradeActions
- `NEXT_PUBLIC_REDIS_URL` — never expose Redis URL to browser
- Exchange credentials in any form

## Environment Variables

| Variable | Scope | Default | Description |
|----------|-------|---------|-------------|
| `REDIS_URL` | Server-side only | (none) | Redis connection URL. When set, adapter attempts connection. |
| `REDIS_CONNECTION_STRING` | Server-side only | (none) | Alternative Redis URL variable name. |

**Redis URL is NEVER exposed to the browser.** It stays in server-side environment only.

## Files

| File | Purpose |
|------|---------|
| `packages/tradehud_contracts/redis_adapter.py` | RedisStreamAdapter + stream entry parsers |
| `services/api/routes/tradehud_sse.py` | SSE route with Redis/mock source selection |
| `tests/tradehud_contracts/test_redis_adapter.py` | Adapter unit tests |
| `tests/web/test_tradehud_sse_redis.py` | SSE Redis integration tests |

## Usage

### Automatic (recommended)

Set `REDIS_URL` in the server environment. The SSE route detects it automatically:

```bash
export REDIS_URL="redis://localhost:6379"
# Start Builder API — SSE route will use Redis if reachable
```

If Redis is unreachable, the route falls back to mock data with `provenance: "mock"`.

### Manual testing with fakeredis

```python
import fakeredis.aioredis
from packages.tradehud_contracts.redis_adapter import RedisStreamAdapter

adapter = RedisStreamAdapter(redis_url="redis://localhost:6379")
# Inject fake client for testing
adapter._client = fakeredis.aioredis.FakeRedis()
adapter._connected = True
snapshot = await adapter.get_snapshot("BTCUSDT-PERP")
```

## What This Branch Adds

- `RedisStreamAdapter` — read-only XREAD consumer for 12 ND runtime streams
- Automatic source selection in SSE route (Redis → mock fallback)
- Stream entry parsers for all TradeHUD contract models
- Per-stream caching with `XREAD BLOCK` for responsive reads
- Provenance tracking: `redis`/`live` when connected, `mock`/`synthetic` when fallback
- Periodic Redis reconnection check during SSE stream
- Clean disconnect on client unmount
- Comprehensive test coverage (parsing, safety, fallback behavior)

## What This Branch Does NOT Add

- Real exchange execution controls
- Browser-side Redis access
- Redis write operations (XADD, SET, etc.)
- Authentication / authorization model
- Operator command controls
- Kill-switch controls
- Submit/cancel/modify order controls

## Next Steps

After this adapter is accepted:
1. **ND runtime publisher** — implement the ND-side code that XADDs events to the stream keys
2. **Stream consumer groups** — use consumer groups for multi-instance SSE scaling
3. **Historical replay** — store stream snapshots for backfill/replay from a point in time
