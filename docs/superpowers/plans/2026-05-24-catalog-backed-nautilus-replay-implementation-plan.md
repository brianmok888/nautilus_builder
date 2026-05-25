# Catalog-Backed NautilusTrader Replay Implementation Plan

> Required execution discipline: `superpowers:test-driven-development` for each behavior change. Execute as segment-gated autopilot-style loops with reconciliation before moving on.

## Segment 1 — Catalog-backed replay smoke

1. RED: Add `tests/backtest_runner/test_catalog_backed_nautilus_replay_smoke.py` expecting `run_catalog_backed_nautilus_replay_smoke()` and `CATALOG_BACKED_REPLAY_SMOKE_MODE` to exist and report catalog path, data count, strategy path, result metrics, zero orders, and no authority.
2. GREEN: Implement `packages/backtest_runner/catalog_replay_smoke.py` using `ParquetDataCatalog`, deterministic Nautilus quote ticks, `BacktestNode`, `BacktestDataConfig`, `BacktestVenueConfig`, `BacktestEngineConfig`, and `SubscribeStrategy`.
3. Export the function/mode from `packages/backtest_runner/__init__.py`.
4. Verify focused backtest runner smoke tests.
5. Reconcile ledgers.

## Segment 2 — Evidence language and readiness boundaries

1. RED: Add/update README or integration guard tests so docs distinguish empty lifecycle smoke from catalog-backed replay smoke and still avoid full production overclaiming.
2. GREEN: Update README and hardguard wording.
3. Verify focused docs/readiness tests.
4. Reconcile ledgers.

## Segment 3 — Master reconciliation

1. Run full Python compile/test suite.
2. Run frontend typecheck/unit/build/E2E.
3. Run authority grep for live-order/credential/Daedalus execution terms.
4. Update `structure.md`, `findings.md`, and `handguard.md` with master status.
