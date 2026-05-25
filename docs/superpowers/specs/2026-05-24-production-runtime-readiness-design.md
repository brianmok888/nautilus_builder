# Production runtime readiness closure design

Date: 2026-05-24
Repo: Nautilus Builder (`/home/mok/projects/nautilus_builder`)

## Goal

Close the remaining production-readiness blockers without changing Builder's authority boundary. Builder may author, validate, compile, run catalog-backed backtest/signal-preview evidence, persist artifacts, and expose observational APIs. Builder must not gain live order authority, Daedalus execution-lane imports, shell authority, broker/exchange order paths, or credential handling.

## Source-truth constraints

- `doc/nautilus_builder_hardguards.md` remains the safety source of truth.
- NautilusTrader evidence must use the pinned local/runtime `nautilus_trader==1.223.0` guard.
- Official NautilusTrader backtesting/data patterns use `ParquetDataCatalog`, `BacktestDataConfig`, `BacktestRunConfig`, `BacktestVenueConfig`, and `BacktestNode` for catalog-backed replay.
- User-selected datasets and artifacts must be project/user scoped before any production-readiness claim.

## Chosen approach

Implement a minimal production-readiness spine in five bounded segments:

1. **Durable artifact storage**: add a local JSON artifact store with deterministic `artifact://builder/...` refs, checksums, metadata, and user/project scope checks. This is a durable local adapter, not an object-store replacement.
2. **Catalog dataset registry**: add a project-scoped catalog dataset registry and selection contract. Dataset selection validates adapter, instrument, data type, timeframe, market type, and date range before backtest jobs can claim dataset readiness.
3. **StrategySpec-generated replay**: add a no-order Nautilus `RuleGraphBacktestStrategy` and replay runner that serializes the validated StrategySpec into BacktestNode strategy config, replays deterministic local catalog data, and records evidence that the strategy path came from Builder's compiled StrategySpec path rather than the generic subscribe smoke.
4. **Authz/tenant controls**: extend backtest jobs with `user_id`, `project_id`, `dataset_id`, and `catalog_path`; add scoped access checks in service/API seams and artifact reads.
5. **CI/deployment evidence**: update CI template and deployment evidence docs/tests so readiness claims cite the Python contract suite, Nautilus runtime smoke checks, frontend type/unit/build/e2e checks, and deployment hardguards.

## Non-goals

- No live or paper order execution.
- No Daedalus imports or edits.
- No external market-data downloads in tests.
- No production object-store/S3 adapter in this pass.
- No broad frontend UX redesign.

## Acceptance criteria

- Backtest artifacts survive a new store instance and reject cross-project access.
- Catalog dataset selection is explicit, tenant-scoped, and rejects mismatched dataset/job/spec fields.
- StrategySpec-generated Nautilus replay evidence uses Builder's `RuleGraphBacktestStrategy`, a real `ParquetDataCatalog`, and a real `BacktestNode` run, while reporting zero orders/positions and false live authority booleans.
- Backtest jobs expose and enforce scoped user/project fields when a context is supplied.
- CI/deployment evidence files enumerate all required local and CI checks.
- `structure.md`, `findings.md`, and `handguard.md` record segment completions and remaining boundaries.
