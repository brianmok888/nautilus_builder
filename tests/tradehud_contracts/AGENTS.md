# AGENTS — tests/tradehud_contracts (+ tests/tradehud_redis)

Contract enforcement for the TradeHUD ND runtime + redis adapter. These tests are the executable contract for `packages/tradehud_contracts/`.

## Scope
- `test_nd_fixture_loading.py` — loads the `tests/fixtures/tradehud_nd_contracts/*.jsonl` fixtures and asserts they parse.
- `test_nd_normalizer_contracts.py` — the `missing != true_zero` rule and force-liquidation/trade-flag detection.
- `test_nd_redis_adapter_contracts.py` — `RedisStreamAdapter` parse paths per stream type, snapshot assembly, health sanitization.
- `test_nd_snapshot_contracts.py` — snapshot shape per model.
- `test_nd_freshness_contracts.py` — `SourceFreshnessMeta` / staleness rules.
- `test_nd_stream_contracts.py`, `test_nd_sse_contracts.py` — stream + SSE payload contracts.
- `test_nd_safety_contracts.py` — read-only / no-order-authority boundaries.
- `../tradehud_redis/test_redis_adapter.py`, `test_health_sanitization.py` — deep redis adapter + URL sanitization.

## Conventions
- Fixtures live in `tests/fixtures/tradehud_nd_contracts/` as `.jsonl` (one ND event per line, 17 fixtures covering book/trade/order/position/quant/signal/gate/tick-to-trade/stale-missing-zero cases).
- Tests import directly from `packages.tradehud_contracts` via repo-root `sys.path` (see `tests/conftest.py`).
- Names are behavior-first: `test_<rule>` (e.g. missing-vs-zero, sanitization, read-only).

## Anti-patterns (THIS PROJECT)
- Never weaken the `missing != true_zero` assertions to make a parse pass.
- Never assert against a raw Redis URL; always the sanitized form.
- Never add tests that assume live ND, real Redis, or order authority.
- Replay through `scripts/tradehud_replay_nd_fixtures.py` must stay green when fixtures change.

## Verification
```bash
pytest tests/tradehud_contracts tests/tradehud_redis -x -q
python3 scripts/tradehud_replay_nd_fixtures.py
```
