# Production runtime readiness closure implementation plan

Date: 2026-05-24
Repo: Nautilus Builder

## Segment 1 — durable artifact storage

TDD:
1. Add tests for local JSON artifact persistence, checksum refs, and cross-project rejection.
2. Implement `packages/artifact_store` models/service.
3. Export public API and update ledgers.

Verification:
- `rtk pytest tests/artifact_store -q`

## Segment 2 — user-selected catalog datasets

TDD:
1. Add tests for registering/selecting tenant-scoped catalog datasets and rejecting mismatches/cross-project access.
2. Implement `packages/catalog_datasets` models/service.
3. Add `dataset_id`/`catalog_path` fields to backtest job payloads without breaking legacy tests.
4. Update ledgers.

Verification:
- `rtk pytest tests/catalog_datasets tests/backtest_jobs -q`

## Segment 3 — StrategySpec-generated catalog replay

TDD:
1. Add a test that a StrategySpec payload runs through catalog-backed replay with Builder's rule-graph strategy path, not the subscribe-only smoke.
2. Implement Nautilus `RuleGraphBacktestStrategyConfig`/`RuleGraphBacktestStrategy` as a no-order replay strategy.
3. Implement `run_strategy_spec_catalog_replay` that validates/compiles the StrategySpec, validates dataset match, writes/uses deterministic local catalog data, runs BacktestNode, and returns evidence.
4. Update worker to optionally store replay artifacts when a dataset/spec payload is present.
5. Update ledgers.

Verification:
- `rtk pytest tests/backtest_runner/test_strategy_spec_catalog_replay.py tests/backtest_runner/test_worker_integration.py -q`

## Segment 4 — authz/tenant controls

TDD:
1. Add service/API tests for scoped job access and denial across user/project boundaries.
2. Implement optional `UserProjectContext` checks for get/cancel/transition and route query/payload context extraction.
3. Update ledgers.

Verification:
- `rtk pytest tests/auth tests/backtest_jobs tests/api/test_backtest_job_routes.py -q`

## Segment 5 — CI/deployment evidence

TDD:
1. Add integration tests asserting CI/deployment evidence covers lock sync, Nautilus runtime smoke, Python contracts, frontend type/unit/build/e2e, and no-live-authority deployment guard.
2. Update `infra/ci/github-actions-test.yml`, deployment evidence docs, and README limitations.
3. Update ledgers.

Verification:
- `rtk pytest tests/integration/test_operability_baseline.py tests/integration/test_readme_readiness_hygiene.py -q`

## Master reconciliation

Run:

```bash
python3 -m compileall -q packages services tests
rtk pytest tests/strategy_spec tests/strategy_validation tests/adapter_registry tests/instrument_registry tests/strategy_compiler tests/backtest_jobs tests/runtime_events tests/backtest_runner tests/lifecycle tests/strategy_registry tests/promotions tests/web tests/ai_builder tests/integration tests/workflow_spine tests/auth tests/api tests/artifact_store tests/catalog_datasets -q
cd apps/web && npm run typecheck && npm test && npm run build && npm run test:e2e
rg -n "submit_order|TradeAction|api_key|secret_key|credential|broker_order|exchange_order|run_execution_lane|nautilus_brain|nautilus_runtime" packages services apps/web tests --glob '!**/__pycache__/**' -S
git diff --check
```
