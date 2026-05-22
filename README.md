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
- `apps/web/components/` — placeholder TSX components that encode UI boundary intent only

## What exists today

Implemented seam packages currently cover:
- StrategySpec schema and JSON schema export
- hard-rule validation
- adapter/instrument registry scaffolding
- StrategySpec compilation
- durable backtest job/runtime event scaffolding
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

- no package manifest or CI workflow yet
- no real API server bootstrap yet
- no real frontend app shell or frontend build pipeline yet
- TSX files are placeholders aligned to Python contract tests, not interactive UI implementation
- verification is still contract-heavy and scaffold-oriented rather than production-integrated
