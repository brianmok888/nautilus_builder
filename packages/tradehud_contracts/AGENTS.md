# TradeHUD Python contract knowledge base

## OVERVIEW
Read-only ND payload normalization and snapshot contracts; score 8, the Python display-contract authority.

## WHERE TO LOOK
| Task | Module | Responsibility |
|---|---|---|
| Runtime payload models | models.py | Book, trade, signal, gate, report and account contracts |
| Field normalization | normalizer.py | parse_stream_entry and missing/zero distinction |
| Redis consumption | redis_adapter.py | Async read adapter facade |
| Adapter internals | redis_snapshot_builder.py, redis_normalizers.py, stream_health.py | Assembly, parsing and health |
| Stream configuration | config.py | Stream maps and sanitized URLs |
| Default snapshot provider | service.py | Deterministic mock/replay snapshots |
| Synthetic payloads | mock_data.py | Mock generation |
| Public surface | __init__.py | Intended package imports |

## CONVENTIONS
- Snapshot freshness metadata stays explicit through SourceFreshnessMeta.
- Absent numeric fields stay None; a supplied 0 remains a true zero.
- Parse raw stream entries once through parse_stream_entry.
- Await adapter connect, snapshot and health operations.
- Distinguish Redis-enabled configuration from complete Redis configuration.
- TradeHudService itself is mock-only; API wiring chooses the Redis path separately.
- Health must identify provenance and sanitize the Redis connection URL.
- TS types mirror these models, not the other way around.
- Verify with python3 -m pytest tests/tradehud_contracts tests/tradehud_redis -x -q.
- Fixture replay uses python3 scripts/tradehud_replay_nd_fixtures.py.

## ANTI-PATTERNS
- Do not add ND stream writes, order placement or credential handling here.
- Do not collapse missing and zero to make a payload parse.
- Do not return raw REDIS_URL values in health or snapshot output.
- Do not couple model definitions to React implementation details.
