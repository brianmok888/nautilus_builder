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
- `packages/` holds real domain logic and models. See `packages/AGENTS.md`.
- `services/api/routes/` holds thin adapter-style route stubs over `packages/*`. See `services/api/AGENTS.md`.
- `services/workers/` holds worker entrypoint stubs.
- `tests/` mirrors feature seams; tests are policy/contract-first. See `tests/AGENTS.md`.
- `apps/web/` is a Next.js 15 + Ant Design 6 + React 19 frontend. See `apps/web/AGENTS.md`.
- `doc/` is source-truth spec. See `doc/AGENTS.md`.

## AGENTS.md hierarchy
```
./AGENTS.md                 (this file)
├── apps/web/AGENTS.md      (TypeScript frontend domain)
├── apps/web/components/AGENTS.md  (UI component boundaries)
├── doc/AGENTS.md           (spec source truth)
├── packages/AGENTS.md      (domain layer conventions)
├── services/api/AGENTS.md  (route adapter conventions)
└── tests/AGENTS.md         (test conventions)
```

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
pytest tests/ -x -q                    # full suite, fail-fast
pytest tests/execution_lane tests/workflow_spine tests/backtest_runner -x -q  # heavy seams
cd apps/web && npx vitest run           # frontend unit tests
cd apps/web && npx playwright test      # e2e shell tests
```
