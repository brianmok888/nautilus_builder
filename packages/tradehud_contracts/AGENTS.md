# AGENTS — packages/tradehud_contracts

Python source of truth for the TradeHUD ND (NautilusTrader-Daedalus) runtime contract. Read-only observational monitor, not a runtime authority.

## Scope
- `models.py` — Pydantic v2 models for every ND runtime payload (book top, book L2, trades, signals, gate decisions, trade-action evidence, execution reports, account/position/open-order/asset snapshots, quant levels, tick-to-trade traces, lane + runtime health). All snapshot models extend `SourceFreshnessMeta`.
- `normalizer.py` — Redis Stream entry normalizer. Enforces `missing != true_zero`: absent fields stay `None`; explicit `0` is a real zero. Parses stream fields, detects force-liquidation + trade flags.
- `redis_adapter.py` — `RedisStreamAdapter`: async read-only consumer of ND Redis Streams. Parses each stream type via `_parse_*`, builds `TradeHudSnapshot` via `build_snapshot_from_redis`. Reports health without leaking the Redis URL.
- `service.py` — `TradeHudService`: read-only snapshot provider over mock data + adapter. Default symbol `BTCUSDT-PERP`.
- `config.py` — `TradeHudRedisConfig`: env-driven stream map, key list, sanitized URL. `is_redis_enabled` vs `is_redis_configured` are distinct.
- `mock_data.py` — deterministic mock fixtures for the no-Redis fallback path.

## Conventions
- All public models are strict Pydantic; prefer `Optional`/`None` over sentinel values.
- `parse_stream_entry(logical_name, fields)` is the single normalization entrypoint; never parse raw fields downstream.
- Adapter methods are `async`; callers must `await` `connect()`/`get_snapshot()`/`get_health()`.
- Health output must be URL-sanitized (`sanitize_redis_url()`); never log raw `REDIS_URL`.

## Anti-patterns (THIS PROJECT)
- Never give this package write authority over ND or order placement — read-only.
- Never collapse `missing` into `0` (or vice versa) in the normalizer; the distinction is a tested contract.
- Never expose the raw Redis URL in health/snapshot output.
- Never couple these models to the TSX layer; the frontend reducer consumes normalized JSON only.

## Verification
```bash
pytest tests/tradehud_contracts tests/tradehud_redis -x -q
python3 scripts/tradehud_replay_nd_fixtures.py   # replay ND jsonl fixtures through normalizer+adapter
```
