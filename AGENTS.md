# AGENTS

## Repo reality
- Repo is no longer docs-only. Real code lives under `packages/`, `services/`, `tests/`, and placeholder UI stubs under `apps/web/components/`.
- `doc/` is still source truth for product/runtime rules.
- `docs/superpowers/` is still derived planning/execution output from `doc/`.
- A minimal Python manifest, CI workflow template, local infra composition, and Next.js app shell now exist; CI activation and production integration remain incremental.

## Read first
- `doc/README.md` for product identity.
- `doc/nautilus_builder_spec.md` and `doc/nautilus_builder_hardguards.md` for runtime/safety boundaries.
- `packages/strategy_spec/models.py`, `packages/strategy_validation/validators.py`, and `packages/backtest_runner/config_builder.py` for current contract truth.
- `tests/` for what is actually enforced today.
- `docs/superpowers/` only after you understand `doc/`; it is interpretation, not primary truth.

## Structure that matters
- `packages/` holds real domain logic and models.
- `services/api/routes/` holds thin adapter-style route stubs over `packages/*`.
- `services/workers/` holds worker entrypoint stubs.
- `tests/` mirrors feature seams; tests are policy/contract-first.
- `apps/web/components/` is mounted by a minimal Next.js app shell; rich interactive runtime/data wiring remains incremental.

## What agents get wrong here
- Do not trust older docs that say `apps/web`, `services/api`, `packages/*`, or `tests/` are only planned; they now exist, but many files are still minimal scaffolds.
- Do not treat the minimal TSX shell as full production UX or runtime authority.
- Do not treat Nautilus-Daedalus as editable from this repo; Builder-side contracts only.
- Do not weaken `UX must not own runtime`.
- Do not give Builder live order authority; `submit_order`, `TradeAction`, and execution-lane behavior stay external.
- Keep names distinct: Nautilus Builder = product, Strategy Builder = one module, NautilusTrader = engine, Nautilus-Daedalus = live control system.

## Verified conventions
- `doc/` uses flat `nautilus_builder_*` snake_case filenames.
- `docs/superpowers/` uses dated `YYYY-MM-DD-...` filenames grouped by artifact type.
- `packages/*` usually expose `models.py`, `service.py`, or seam-specific helpers; `__init__.py` re-exports the public surface.
- `services/api/routes/*` should stay thin and mostly `model_dump(mode="json")` package outputs.
- `tests/*` mirror package/feature names and assert boundaries, not rich integration frameworks.
- `tests/conftest.py` adds repo root to `sys.path`; tests import directly from `packages.*`.

## Useful checks
```bash
git status
grep -R "Do not\|must not\|forbidden" doc docs/superpowers
rtk pytest tests/strategy_spec tests/strategy_validation tests/adapter_registry tests/instrument_registry tests/strategy_compiler tests/backtest_jobs tests/runtime_events tests/backtest_runner tests/lifecycle tests/strategy_registry tests/promotions tests/web tests/ai_builder tests/integration
```
