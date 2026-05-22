# AGENTS

## Scope
- `packages/` is the canonical implementation layer.
- Put domain rules, models, validators, compilers, registries, and verification helpers here.

## Conventions
- Keep one bounded seam per package: `strategy_spec`, `strategy_validation`, `backtest_runner`, `lifecycle`, `promotions`, etc.
- Export the intended public surface from each package `__init__.py`.
- Favor strict Pydantic models and explicit booleans/enums over loose dict contracts.
- Keep route/worker concerns out of package modules.

## Current patterns
- `strategy_spec` + `strategy_validation` define schema and hard-rule truth.
- `strategy_compiler`, `backtest_jobs`, `runtime_events`, and `backtest_runner` model backend-owned execution flow.
- `ui_contracts` defines behavior contracts used by tests; it is not a real frontend runtime.
- `system_verification` is a composed verification harness, not production orchestration.

## Do not
- Do not import Nautilus-Daedalus internals.
- Do not create live order authority in Builder.
- Do not hide policy boundaries in UI stubs or route wrappers.
- Do not bypass validation/lifecycle checks when adding new seams.

## Verification
- Prefer focused seam tests first, then broader suite slices.
- Keep deterministic outputs where possible: stable hashes, fixed artifact names, explicit error strings.
