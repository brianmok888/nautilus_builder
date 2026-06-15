# TradeHUD Redis Stream Adapter

## Scope

Read-only Redis Stream consumer that reads Nautilus-Daedalus (ND) runtime events
from Redis Streams and feeds them into the TradeHUD SSE route.

**This branch does NOT implement execution authority.**
**This branch does NOT submit, cancel, or modify orders.**
**Only `run_execution_lane` may call `submit_order(...)`.**

## Architecture

```
Browser ──SSE──▶ FastAPI SSE Route ──▶ Redis Stream Adapter ──XREAD──▶ Redis Streams
                              │
                              └── Mock/Synthetic (fallback)
```

The browser **never** connects directly to Redis.
The browser **never** receives Redis credentials or exchange secrets.

## Branch Safety Boundary

- **No `submit_order` calls** in adapter or SSE route
- **No `NEXT_PUBLIC_REDIS_URL`** — Redis URL is server-side only
- **No exchange API keys** in any frontend code
- **No POST/PUT/DELETE routes** in TradeHUD SSE endpoints
- **No direct browser-to-Redis connections**
- **Read-only Redis ops only**: `XREAD`, `XREVRANGE` (no `XADD`, `SET`, `PUBLISH`)
- **Seeder** (`scripts/tradehud_seed_redis.py`) is LOCAL DEVELOPMENT ONLY

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TRADEHUD_FEED_SOURCE` | `mock` | Feed source: `mock` or `redis` |
| `TRADEHUD_REDIS_URL` | (none) | Redis connection URL (server-side only) |
| `TRADEHUD_STREAM_NAMESPACE` | `nd` | Stream namespace: `nd`, `nautilus_tradehud`, or custom |
| `TRADEHUD_REDIS_BLOCK_MS` | `1000` | XREAD block timeout in ms |
| `TRADEHUD_REDIS_COUNT` | `100` | Max entries per XREAD call |
| `TRADEHUD_STREAM_STALE_MS` | `3000` | Stream staleness threshold |
| `TRADEHUD_STREAM_MISSING_MS` | `10000` | Stream missing threshold |

### Custom Stream Overrides

Individual streams can be overridden:
```
TRADEHUD_STREAM_BOOK_TOP=custom.book.top
TRADEHUD_STREAM_TRADES=custom.trades
```

## Stream Namespace Config

### `nd` namespace (default)

| Logical Name | Stream Key | Description |
|-------------|-----------|-------------|
| `book_top` | `nd.market.book_top` | Top-of-book bid/ask |
| `book_l2` | `nd.market.book_l2` | L2 order book depth |
| `trades` | `nd.market.trades` | Trade tape |
| `bars` | `nd.market.bars` | OHLCV bars |
| `state_bundle` | `nd.state_bundle` | Strategy state |
| `feature_snapshot` | `nd.feature_snapshot` | Feature vector |
| `signal` | `nd.strategy_signal_preview` | Signal preview |
| `gate` | `nd.gate_decision` | Gate decision |
| `trade_action` | `nd.trade_action` | Trade action (evidence only) |
| `execution` | `nd.execution_report` | Execution report |
| `account` | `nd.account.snapshot` | Account snapshot |
| `positions` | `nd.position.snapshot` | Position snapshot |
| `orders` | `nd.order.snapshot` | Open orders |
| `order_events` | `nd.order.event` | Order lifecycle events |
| `quant_levels` | `nd.quant_levels.context` | Quant levels |
| `tick_to_trade` | `nd.tick_to_trade.trace` | T2T trace |
| `health` | `nd.health` | Runtime health |

### `nautilus_tradehud` namespace (legacy)

Uses `nautilus:tradehud:*` prefix for backward compatibility.

## Event Payload Shapes

Redis stream entries support three incoming formats:

### 1. Flat fields
```
symbol=BTCUSDT-PERP
price=67250.5
qty=0.021
side=BUY
```

### 2. JSON payload
```
payload={"symbol": "BTCUSDT-PERP", "price": 67250.5}
```

### 3. Envelope
```
event_type=market_trade
schema_version=1
payload={"symbol": "BTCUSDT-PERP", "price": 67250.5}
```

## Normalization Rules

**Missing fields ≠ true zero.**

| Scenario | Behavior |
|----------|----------|
| `price` missing | Record rejected (required field) |
| `qty` missing | Record rejected (required field) |
| `ts_event_ns` missing | `source_status: "unknown"` |
| `bid_size=0` | Explicit zero — preserved |
| `bid_size` missing | `None` — not zero |
| `notional` missing | `None` — computed from price × qty if both present |

### Missing vs True Zero

```python
# BAD: defaults missing to zero
_to_float(value, default=0.0)

# GOOD: missing stays None
to_optional_float(None)  # → None
to_optional_float("")    # → None
to_optional_float("0")    # → 0.0
```

### Binance Futures Liquidation

```
SELL + force_order → LONG_LIQ flag
BUY  + force_order → SHORT_LIQ flag
```

## Freshness Rules

| Status | Condition |
|--------|-----------|
| `live` | Event received within `TRADEHUD_STREAM_STALE_MS` |
| `stale` | Event exists but older than `TRADEHUD_STREAM_STALE_MS` |
| `missing` | Stream never seen and older than `TRADEHUD_STREAM_MISSING_MS` |
| `unavailable` | Redis connection lost |
| `unknown` | Event timestamp missing |
| `synthetic` | Seeded/mock data |

## Per-Stream Health Tracking

Each stream tracks:
- `stream_name`, `logical_name`
- `last_entry_id`, `last_event_ts_ns`, `last_receive_ts_ns`
- `age_ms`, `events_seen`, `last_error`
- `status` (live/stale/missing/unavailable/unknown/synthetic)

Emitted as SSE `stream_health` events.

## Local Redis Seeder Flow

```bash
# Terminal 1: Redis
redis-server

# Terminal 2: Seeder
python scripts/tradehud_seed_redis.py \
  --redis-url redis://127.0.0.1:6379/0 \
  --namespace nd \
  --symbols BTCUSDT-PERP ETHUSDT-PERP \
  --interval-ms 1000

# Terminal 3: API server
TRADEHUD_FEED_SOURCE=redis \
TRADEHUD_REDIS_URL=redis://127.0.0.1:6379/0 \
TRADEHUD_STREAM_NAMESPACE=nd \
python -m services.api.dev_server

# Terminal 4: Frontend
NEXT_PUBLIC_TRADEHUD_FEED_MODE=sse \
NEXT_PUBLIC_BUILDER_API_BASE=http://127.0.0.1:8000 \
npm run dev
```

Open `/tradehud`:
- Feed: SSE REDIS
- Redis: Connected
- Stream health visible
- Book/tape/signals update
- `NO BROWSER ORDER AUTHORITY` visible
- `OBSERVATIONAL` · `NOT EXECUTABLE` visible
- Seeded events show `provenance: seeded_mock`, `source_status: synthetic`

Stop Redis → Redis disconnected/degraded visible, UI does not crash.

## Manual Test Flow

1. Start Redis + Seeder + API + Frontend (above)
2. Verify SSE events in browser DevTools → Network → EventStream
3. Verify `/api/tradehud/health` shows `feed_source: redis`
4. Verify `/api/tradehud/health` does NOT contain Redis password
5. Stop Redis → health shows `redis_connected: false`
6. Verify browser shows `REDIS DISCONNECTED` badge
7. Restart Redis → adapter reconnects automatically

## Known Limitations

- Adapter only reads from Redis Streams — does not manage consumer groups
- No historical replay — only latest entry per stream is seeded on connect
- Stream health is based on wall-clock time, not exchange timestamps
- Seeder data is deterministic but not representative of live market microstructure
- No multi-instance scaling — single XREAD consumer per stream

## Next Branch

- Consumer group support for multi-instance SSE scaling
- Historical replay from Redis keys (not just latest)
- Exchange timestamp-based freshness (not wall-clock)
- ND runtime publisher integration
