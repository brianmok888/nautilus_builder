# TradeHUD ND Runtime Contract Tests

## Scope

This branch adds a comprehensive contract test layer between Nautilus-Daedalus (ND) / NautilusTrader runtime events and the Nautilus Builder TradeHUD ingestion pipeline. The goal is to verify that the Builder API Redis adapter, SSE gateway, frontend reducer, and TradeHUD UI correctly consume real ND-style runtime events without weakening the safety boundary.

**No new UI features. No execution controls. No browser Redis access.**

## Architecture

```
Nautilus-Daedalus / NautilusTrader runtime
  → Redis Streams using nd.* stream names
    → Builder API Redis adapter (read-only: XREAD/XREVRANGE)
      → normalized TradeHUD event models
        → Builder API SSE route
          → browser EventSource client
            → TradeHUD reducer
              → TradeHUD UI
```

### Safety Boundary

This branch does not add order authority.
This branch does not submit, cancel, or modify orders.
This branch does not connect browser directly to Redis.
This branch does not make Builder the Nautilus-Daedalus runtime.

Only `run_execution_lane` may call `submit_order()`.

## Supported nd.* Streams

### Required streams (contract-tested)

| Logical Name | Redis Stream Key |
|---|---|
| book_top | `nd.market.book_top` |
| book_l2 | `nd.market.book_l2` |
| trades | `nd.market.trades` |
| signal | `nd.strategy_signal_preview` |
| gate | `nd.gate_decision` |
| trade_action | `nd.trade_action` |
| execution | `nd.execution_report` |
| health | `nd.health` |

### Optional streams (contract-tested)

| Logical Name | Redis Stream Key |
|---|---|
| account | `nd.account.snapshot` |
| positions | `nd.position.snapshot` |
| orders | `nd.order.snapshot` |
| order_events | `nd.order.event` |
| quant_levels | `nd.quant_levels.context` |
| tick_to_trade | `nd.tick_to_trade.trace` |
| bars | `nd.market.bars` |

### Legacy namespace

Legacy `nautilus:tradehud:*` streams are still supported via `TRADEHUD_STREAM_NAMESPACE=nautilus_tradehud`.

## Fixture Format

Fixtures live in `tests/fixtures/tradehud_nd_contracts/` as JSONL files (one JSON record per line).

Each record supports three payload shapes:
1. **Flat fields**: `{"symbol": "BTCUSDT-PERP", "price": "50000", ...}`
2. **JSON payload envelope**: `{"payload": "{...json...}"}`
3. **Event envelope**: `{"event_type": "market_trade", "schema_version": "1", "payload": "{...}"}`

All fixtures use deterministic timestamps (base: `1700000000000000000` ns) and deterministic prices (BTC: 50000.0, ETH: 3000.0).

### Fixture files

| File | Purpose |
|---|---|
| `nd_market_book_top.jsonl` | Book top for BTC and ETH |
| `nd_market_book_l2.jsonl` | L2 orderbook depth |
| `nd_market_trades.jsonl` | Market trades (buy/sell, large/sweep) |
| `nd_strategy_signal_preview.jsonl` | Signal previews (NOT EXECUTABLE) |
| `nd_gate_decision.jsonl` | APPROVED / REJECTED / HOLD decisions |
| `nd_trade_action.jsonl` | Runtime-consumed trade action evidence |
| `nd_execution_report.jsonl` | FILLED / REJECTED execution reports |
| `nd_health.jsonl` | Runtime lane health (all healthy) |
| `nd_quant_levels_context.jsonl` | Support/resistance/pivot levels |
| `nd_tick_to_trade_trace.jsonl` | Tick-to-trade latency trace |
| `nd_account_snapshot.jsonl` | Account balance/equity/margin |
| `nd_position_snapshot.jsonl` | Open positions |
| `nd_order_snapshot.jsonl` | Open orders |
| `nd_order_event.jsonl` | Order fill event |
| `nd_mixed_runtime_sequence.jsonl` | Coherent multi-event sequence |
| `nd_bad_missing_fields.jsonl` | Malformed records (must be rejected) |
| `nd_stale_missing_true_zero_cases.jsonl` | Stale/missing/true_zero edge cases |

## Event Normalization Expectations

- Missing numeric fields → `None` (never silently converted to 0)
- Explicit zero → stays 0
- Missing timestamp → record rejected or marked `source_status="unknown"`
- Missing != true_zero

### StrategySignalPreview
- NOT EXECUTABLE
- Never becomes TradeAction
- May contain direction/confidence/entry_hint/target_hint/invalidation_hint
- Must carry feature/context/trace hashes if provided

### GateDecision
- Shows APPROVED / HOLD / REJECTED
- Includes `first_blocking_gate` when rejected/hold
- Includes `reason_code`, `confidence_delta`, `size_modifier`, `gate_decision_hash`
- Does not become execution evidence

### TradeAction
- Runtime-consumed evidence only
- Must include `trade_action_hash`
- Must include `source_gate_decision_hash`
- Must not be created by browser or Builder API

### ExecutionReport
- Runtime/exchange evidence
- Status: SUBMITTED / ACKED / LIVE / PARTIAL_FILL / FILLED / CANCELED / REJECTED / EXPIRED
- Must link to `trade_action_hash`
- Does not imply strategy confidence

## Freshness Rules

| Source Status | Condition |
|---|---|
| `live` | Fresh Redis record, timestamp within threshold |
| `stale` | Redis record exists but timestamp is old |
| `missing` | Stream has no entries |
| `synthetic` | Local mock data only |
| `true_zero` | Source is live but value is explicitly 0 |
| `unavailable` | Redis is disconnected |
| `unknown` | Timestamp missing or unparseable |

## SSE Contract

SSE route emits these event types:
- `snapshot` — initial normalized TradeHUD snapshot
- `tradehud_event` — individual normalized event
- `stream_health` — stream/lane health status
- `ping` — keepalive with server time
- `error` — error status

Redis mode requires `TRADEHUD_FEED_SOURCE=redis`. Generic `REDIS_URL` alone does not activate Redis mode.

## Frontend Reducer Contract

Each ND event type updates only its intended state slice:
- `BOOK_TOP` → `bookTop`
- `BOOK_L2` → `bookL2`
- `TRADE` → `trades[]` (bounded)
- `SIGNAL_PREVIEW` → `latestSignalPreview` (only)
- `GATE_DECISION` → `latestGateDecision` (only)
- `TRADE_ACTION` → `latestTradeAction` (only)
- `EXECUTION_REPORT` → `latestExecutionReport` (only)
- `RUNTIME_HEALTH` → `runtimeHealth`

TradeActionEvidencePanel must not render Submit/Cancel/Modify/Approve/Force controls.

## Local Fixture Replay Flow

### Manual test flow

```bash
# Terminal 1: Start Redis
redis-server

# Terminal 2: Replay fixtures
python scripts/tradehud_replay_nd_fixtures.py \
    --redis-url redis://127.0.0.1:6379/0 \
    --fixture-dir tests/fixtures/tradehud_nd_contracts \
    --namespace nd \
    --interval-ms 500

# Terminal 3: Start API server
TRADEHUD_FEED_SOURCE=redis \
TRADEHUD_REDIS_URL=redis://127.0.0.1:6379/0 \
TRADEHUD_STREAM_NAMESPACE=nd \
python -m services.api.dev_server

# Terminal 4: Start web dev server
NEXT_PUBLIC_TRADEHUD_FEED_MODE=sse \
NEXT_PUBLIC_BUILDER_API_BASE=http://127.0.0.1:8000 \
npm run dev
```

Open `/tradehud` and expect:
- Feed: SSE REDIS
- Redis connected
- nd.* stream health visible
- Trade tape updates
- Signal preview visible as NOT EXECUTABLE
- Gate decision visible
- Trade action evidence visible
- Execution report visible
- NO BROWSER ORDER AUTHORITY visible

## TypeScript / Python Contract Parity

A guardrail test (`test_ts_python_contract_parity.py`) verifies that every Python event type has a matching TypeScript reducer case and type definition. This prevents silent contract drift between backend and frontend.

## Known Limitations

- Playwright e2e tests may not run in all CI environments
- Redis manual test requires local Redis server
- Fixtures are deterministic but simplified — real ND payloads may have additional fields
- The parity check is lexical (pattern match), not full schema validation

## Next Recommended Branch

`feature/tradehud-production-auth-hardening` — add authentication/session model for TradeHUD access control.
