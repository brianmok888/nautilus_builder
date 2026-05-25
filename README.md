# Nautilus Builder

Nautilus Builder is a Builder-side prototype for strategy authoring, validation, compilation, backtest runtime scaffolding, promotion contracts, and verification around NautilusTrader-based workflows.

This repository is intentionally **Builder-only**:
- it does **not** own live order execution,
- it does **not** edit Nautilus-Daedalus,
- and the placeholder UI components do **not** replace backend runtime truth.

## Current repo shape

- `doc/` — source-truth product, architecture, and hardguard docs
- `docs/superpowers/` — derived specs, plans, audits, designs, and prompt artifacts
- `packages/` — canonical Python implementation layer by seam/domain
- `services/api/` — thin route/payload adapters over `packages/*`
- `services/workers/` — worker entrypoint stubs
- `tests/` — feature-mirrored pytest contract suite
- `apps/web/app/` — minimal Next.js app shell mounted over Builder UI components
- `apps/web/components/` — interactive/operator MVP TSX components that still do not own runtime authority
- `pyproject.toml` / `uv.lock` — Python package/dependency manifest and lockfile, including the Daedalus-matched NautilusTrader pin

## What exists today

Implemented seam packages currently cover:
- StrategySpec schema and JSON schema export
- hard-rule validation
- adapter/instrument registry scaffolding
- StrategySpec compilation
- durable backtest job/runtime event scaffolding
- local JSON artifact store for scoped evidence persistence
- tenant-scoped catalog dataset selection contracts
- backtest worker/config/result normalization scaffolding
- lifecycle/versioning policy
- external strategy registry/import rules
- Builder-side promotion contracts
- Python-backed UI contract surfaces
- advisory AI drafting flow
- MVP verification harness

Representative modules:
- `packages/strategy_spec/models.py`
- `packages/strategy_validation/validators.py`
- `packages/strategy_compiler/compiler.py`
- `packages/backtest_jobs/service.py`
- `packages/backtest_runner/config_builder.py`
- `packages/backtest_runner/catalog_replay_smoke.py`
- `packages/backtest_runner/strategy_spec_replay.py`
- `packages/artifact_store/service.py`
- `packages/catalog_datasets/service.py`
- `packages/strategy_registry/service.py`
- `packages/ai_builder/service.py`

## Important boundaries

- `doc/` remains the primary source of truth.
- `docs/superpowers/` is derived guidance, not source truth.
- Builder must remain **contract-only** with respect to Nautilus-Daedalus.
- UX must remain **authoring/observational only** and must not own runtime.
- Builder must not create `TradeAction` or call `submit_order`.
- AI remains advisory only; all output must remain draft-stage and pass Builder validation/lifecycle rules.

## Verification

Focused seam tests can be run by domain, for example:

```bash
rtk pytest tests/strategy_spec
rtk pytest tests/strategy_validation
rtk pytest tests/backtest_runner
```

Full current verification suite:

```bash
rtk pytest tests/strategy_spec tests/strategy_validation tests/adapter_registry tests/instrument_registry tests/strategy_compiler tests/backtest_jobs tests/runtime_events tests/backtest_runner tests/lifecycle tests/strategy_registry tests/promotions tests/web tests/ai_builder tests/integration
```

## Current limitations

Current implemented scaffolds include `pyproject.toml`, `services/api/fastapi_app.py`, `services/api/dev_server.py`, a minimal Next.js app shell, Vitest, Playwright, and passing local build/E2E checks. Remaining limitations are production-integration focused:

- `uv.lock` is present for local dependency reproducibility; CI-validated environment sync is still pending
- the real NautilusTrader evidence now includes a catalog-backed Nautilus replay smoke over synthetic historical quote ticks
- the original catalog-backed Nautilus replay smoke is not a production-scale StrategySpec-generated replay; Builder now also has a StrategySpec-generated catalog replay path using a no-order RuleGraphBacktestStrategy, but that replay still uses deterministic local/synthetic quote-tick data for test evidence
- local JSON artifact store evidence and tenant-scoped catalog dataset contracts exist, but production object-storage provisioning remains deployment work
- route-level scoped access contracts exist, but production still needs real auth middleware/token propagation into those package checks
- promotion requests are shadow/signal-preview only and require evidence before readiness can be claimed
- verification remains contract-heavy and local; production deployment, object storage, and CI gates remain incremental
