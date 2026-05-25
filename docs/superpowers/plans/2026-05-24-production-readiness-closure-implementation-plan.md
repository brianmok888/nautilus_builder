# Nautilus Builder Production-Readiness Closure Implementation Plan

> REQUIRED SUB-SKILLS: `superpowers:test-driven-development`; Nautilus work routes through `superpowers:nt` with `nt-backtest`, `nt-testing`, `nt-review`, and `nt-architect` lenses. `superpowers:aiogram-dialog-menus` is loaded but no Telegram dialog changes are in scope.

## Segment 1 — Runtime dependency truth

1. RED: add tests for runtime version check mismatch/match and actual installed NautilusTrader distribution matching `NAUTILUS_TRADER_VERSION`.
2. GREEN: add `packages/backtest_runner/runtime_check.py` and export it.
3. Environment: sync/install `nautilus_trader==1.223.0` for the active local Python used by verification.
4. Verify focused backtest dependency tests.
5. Update `structure.md`, `findings.md`, `handguard.md`.

## Segment 2 — Real NautilusTrader BacktestEngine smoke

1. RED: add test expecting a real smoke mode separate from `fixture` and `injected_engine`.
2. GREEN: add `packages/backtest_runner/real_engine_smoke.py` with quiet `BacktestEngine` lifecycle run.
3. Verify focused smoke/backtest-runner tests.
4. Update ledgers.

## Segment 3 — Promotion evidence hardening

1. RED: update/add tests proving `/api/promotions/shadow` rejects missing evidence and accepts explicit evidence only.
2. GREEN: require `PromotionEvidenceRefs`/explicit refs in service and API route.
3. Verify promotions/API route tests.
4. Update ledgers.

## Segment 4 — StrategySpec docs/schema alignment

1. RED: add tests for documented executable indicators/operators and logical-combinator docs wording.
2. GREEN: extend schema for safe indicator/comparison names and clarify docs for `all`/`any` combinators.
3. Verify strategy_spec/strategy_validation tests.
4. Update ledgers.

## Segment 5 — Readiness hygiene

1. RED: update tests for `db_schema` and alias behavior; add warning-free import/config construction check.
2. GREEN: rename `BuilderPostgresConfig.schema` to `db_schema` with alias support; update README limitations.
3. Verify workflow_spine tests and frontend E2E startup.
4. Update ledgers.

## Master reconciliation

1. Run compileall/full Python suite/frontend typecheck/unit/build/E2E.
2. Grep for authority creep: `submit_order`, `TradeAction`, credentials, Daedalus imports.
3. Update ledgers with master status and final recommendation.
