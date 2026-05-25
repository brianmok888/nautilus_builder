# Catalog-Backed NautilusTrader Replay Readiness Design

**Date:** 2026-05-24
**Target repo:** `/home/mok/projects/nautilus_builder`
**Workflow:** `superpowers:brainstorming` design feeding segment-by-segment autopilot-style TDD.
**Nautilus routing:** `superpowers:nt` -> primary `nt-backtest`, supporting `nt-testing` and `nt-review`.

## Goal

Close the remaining trading-production readiness blocker: Builder currently proves only an empty `BacktestEngine` lifecycle. Add a deterministic, catalog-backed NautilusTrader replay smoke that writes historical market data to a `ParquetDataCatalog`, runs a real Nautilus backtest with an importable no-order strategy, and records result/metric evidence without adding live order authority.

Official NautilusTrader backtesting docs state that `BacktestEngine` processes historical data and produces results/metrics, and that `BacktestNode` is the higher-level API that uses `BacktestEngine` internally. This design therefore uses `BacktestNode` plus `ParquetDataCatalog` to prove the exact missing seam: catalog data -> strategy replay -> backtest result.

## Selected approach

### Approach A — deterministic synthetic catalog + official no-order subscribe strategy (selected)

- Build a temporary `ParquetDataCatalog` in the smoke function.
- Write a Nautilus test-kit FX instrument and deterministic quote ticks into the catalog.
- Run `BacktestNode` with `BacktestDataConfig` for `QuoteTick` and official `SubscribeStrategy` configured for quote tick subscription.
- Return evidence with `engine_mode="catalog_backed_replay_smoke"`, catalog data counts, strategy path, run timing, iterations, total orders/positions, and metrics keys.

Why selected:

- Proves real historical data replay through Nautilus' catalog-backed path.
- Avoids live credentials, adapters, Daedalus imports, and order submission.
- Keeps the evidence deterministic and local, with no dataset download.
- Requires minimal new Builder code and remains easy to test.

### Rejected approaches

- **Custom trading strategy submitting orders:** stronger fill evidence, but violates the current Builder no-order-authority posture for this closure pass.
- **Direct `BacktestEngine.add_data` only:** real data but not catalog-backed, so it does not close the stated blocker.
- **External downloaded sample dataset:** closer to production scale, but introduces network/flakiness and does not belong in a deterministic smoke test.

## Boundaries

This smoke may import NautilusTrader test-kit data providers because they are packaged with the pinned Nautilus runtime and avoid external network/data dependencies. It must not import Daedalus, submit orders, create `TradeAction`, use credentials, connect to venues, or claim full strategy performance readiness.

## Acceptance criteria

1. A failing test first proves the current empty smoke is insufficient because it lacks catalog path, data event count, strategy path, and result metrics.
2. The implementation adds a separate `catalog_backed_replay_smoke` mode; it does not relabel fixture, injected, or empty lifecycle modes.
3. The smoke returns evidence that at least five catalog-backed data events were replayed, iterations match data events, result metrics are present, and total orders/positions are zero.
4. `structure.md`, `findings.md`, and `handguard.md` document the new readiness boundary and evidence.
5. Master verification passes and authority grep shows no new live order path.
