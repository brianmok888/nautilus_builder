# Production readiness evidence

Date: 2026-05-24

This file records the Builder-side evidence required before stronger production-readiness claims. It does not grant live trading authority.

## Closed readiness seams

- **durable artifact storage** — `packages/artifact_store` persists JSON evidence with scoped `artifact://builder/...` refs and SHA-256 checksums.
- **user-selected catalog datasets** — `packages/catalog_datasets` requires tenant-scoped dataset selection and validates adapter, instrument, data type, timeframe, market type, and date range.
- **StrategySpec-generated catalog replay** — `packages/backtest_runner/strategy_spec_replay.py` runs validated StrategySpec payloads through Builder's no-order `RuleGraphBacktestStrategy` using Nautilus `ParquetDataCatalog` and `BacktestNode`.
- **authz/tenant controls** — artifacts, datasets, and backtest jobs carry user/project scope and reject cross-project access when a context is supplied.
- **CI/deployment evidence** — `infra/ci/github-actions-test.yml` enumerates Python compile/tests, Nautilus runtime pin check, frontend type/unit/build/e2e checks, and the new storage/dataset suites.

## Non-negotiable deployment boundaries

- Builder has **no live order authority**.
- Builder must not create live trade actions, import Daedalus execution lanes, accept exchange credentials, or route broker/exchange orders.
- StrategySpec replay is backtest/signal-preview evidence only: zero orders, zero positions, no credentials, `execution_authority=False`, and `live_trading_enabled=False`.
- Unscoped legacy route access is compatibility-only; production deployment must inject real auth context into package-level scope checks.
- Local JSON artifacts prove a durable adapter seam, not cloud object-storage operations.

## Required verification commands

```bash
python -m compileall -q packages services tests
python - <<'PY'
from packages.backtest_runner.runtime_check import check_nautilus_runtime_version
status = check_nautilus_runtime_version()
assert status.is_match, status.message
PY
pytest tests/strategy_spec tests/strategy_validation tests/adapter_registry tests/instrument_registry tests/strategy_compiler tests/backtest_jobs tests/runtime_events tests/backtest_runner tests/lifecycle tests/strategy_registry tests/promotions tests/web tests/ai_builder tests/integration tests/api tests/auth tests/workflow_spine tests/artifact_store tests/catalog_datasets
(cd apps/web && npm run typecheck && npm test && npm run build && npm run test:e2e)
```
