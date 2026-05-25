# Nautilus Builder 2026-05-25 Findings Closure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development for every behavior change. This plan is executed inline in this session by segment, with an autopilot-style plan -> implement -> review loop and reconciliation after each segment.

**Goal:** Close the 2026-05-25 review findings around catalog provenance, API auth scope, promotion evidence, registry/replay drift, and no-order semantics.

**Architecture:** Four bounded segments harden catalog/user-data trust, strict API scope, scoped promotion evidence, and StrategySpec replay semantics. Each segment updates tests first, implementation second, then `structure.md`, `findings.md`, and `handguard.md` before the next segment.

**Tech Stack:** Python 3.12, Pydantic v2, pytest/rtk, FastAPI-compatible route seams, NautilusTrader `BacktestNode`/`ParquetDataCatalog`, local JSON artifact store.

---

## File structure

- Modify `packages/catalog_datasets/models.py` — keep dataset metadata strict and source-labeled.
- Modify `packages/catalog_datasets/service.py` — add safe-root path policy and fix mismatch diagnostics.
- Modify `packages/catalog_datasets/__init__.py` — export path policy.
- Modify `packages/backtest_runner/strategy_spec_replay.py` — split synthetic smoke from read-only user replay and record manifest evidence.
- Modify `packages/backtest_runner/__init__.py` — export new smoke helper/constants.
- Modify `services/workers/nautilus_backtest_worker.py` — require/pass catalog root for StrategySpec replay.
- Modify `services/api/routes/backtest_jobs.py` — strict context-derived job creation/read/cancel and profile/dataset validation.
- Modify `services/api/fastapi_app.py` and `services/api/app.py` — wire auth/dataset registry options without weakening dev fixtures.
- Modify `packages/backtest_jobs/models.py` and `packages/backtest_jobs/service.py` — persist validated data profile fields.
- Modify `packages/promotions/models.py` and `packages/promotions/service.py` — carry evidence checksums and strict artifact resolution.
- Modify `services/api/routes/promotions.py` plus API app wiring — strict promotion support where context/store are supplied.
- Modify `packages/instrument_registry/service.py` — align `quote_ticks` availability and validation.
- Modify `packages/strategy_compiler/compiler.py` — rename backtest output mode.
- Modify source-truth docs under `doc/` only where order-intent terminology must be corrected.
- Add/modify focused tests under `tests/catalog_datasets`, `tests/backtest_runner`, `tests/api`, `tests/backtest_jobs`, `tests/promotions`, `tests/instrument_registry`, and `tests/strategy_compiler`.
- Update `structure.md`, `findings.md`, and `handguard.md` after each segment.

## Segment 1 — Catalog trust and real user-catalog replay

- [ ] Write RED tests in `tests/catalog_datasets/test_catalog_dataset_registry.py` for out-of-root catalog rejection, symlink rejection, and corrected expected/got mismatch wording.
- [ ] Write RED tests in `tests/backtest_runner/test_strategy_spec_catalog_replay.py` proving user replay requires `catalog_root`, rejects empty existing catalogs, does not call `TestDataStubs`, and leaves the seeded catalog manifest unchanged.
- [ ] Write/update RED worker integration coverage requiring `catalog_root` for StrategySpec replay.
- [ ] Run focused RED: `rtk pytest tests/catalog_datasets/test_catalog_dataset_registry.py tests/backtest_runner/test_strategy_spec_catalog_replay.py tests/backtest_runner/test_worker_integration.py -q`.
- [ ] Implement `CatalogPathPolicy`, read-only user replay, synthetic smoke helper, manifest evidence, and worker root passing.
- [ ] Run focused GREEN and segment slice: `rtk pytest tests/catalog_datasets tests/backtest_runner -q`.
- [ ] Reconcile `structure.md`, `findings.md`, and `handguard.md` with Segment 1 evidence.

## Segment 2 — Auth-derived API scope and validated backtest job creation

- [ ] Write RED tests in `tests/api/test_backtest_job_routes.py` for strict missing context rejection, spoofed body/query scope ignored, missing required fields returning 422, and dataset/profile validation before job creation.
- [ ] Write RED tests in `tests/api/test_fastapi_app.py` for auth helper/token wiring under fake FastAPI.
- [ ] Write RED package tests if needed for new job audit profile fields.
- [ ] Run focused RED: `rtk pytest tests/api/test_backtest_job_routes.py tests/api/test_fastapi_app.py tests/backtest_jobs -q`.
- [ ] Implement trusted-context route helpers, AuthTokenService FastAPI dependency, dataset registry injection, data profile persistence, and dev-only client-scope compatibility.
- [ ] Run focused GREEN and segment slice: `rtk pytest tests/auth tests/api tests/backtest_jobs tests/catalog_datasets -q`.
- [ ] Reconcile `structure.md`, `findings.md`, and `handguard.md` with Segment 2 evidence.

## Segment 3 — Scoped promotion evidence resolution

- [ ] Write RED tests in `tests/promotions/test_shadow_evidence_contract.py` proving strict mode rejects legacy refs, resolves scoped Builder refs, records checksums, rejects wrong artifact type, and rejects tampered checksum/scope mismatch.
- [ ] Write RED route/helper tests for strict promotion payload behavior when context/store are supplied.
- [ ] Run focused RED: `rtk pytest tests/promotions tests/artifact_store tests/api/test_route_mounts.py -q`.
- [ ] Implement strict artifact resolution in `PromotionService`, add `evidence_checksums`, and wire strict route options.
- [ ] Run focused GREEN and segment slice: `rtk pytest tests/promotions tests/artifact_store tests/api -q`.
- [ ] Reconcile `structure.md`, `findings.md`, and `handguard.md` with Segment 3 evidence.

## Segment 4 — Registry/replay data-type and no-order semantic alignment

- [ ] Write RED tests asserting `BTCUSDT-PERP` exposes/validates `quote_ticks` and StrategySpec replay's data type is visible in market catalog.
- [ ] Update RED compiler/docs tests expecting `backtest_signal_observation` and absence of `backtest_order_intent`/`BacktestOrderIntent` outside historical findings text.
- [ ] Run focused RED: `rtk pytest tests/instrument_registry tests/strategy_compiler tests/backtest_runner -q` plus a grep check.
- [ ] Add `quote_ticks` to registry validation, rename compiler output mode, and correct source-truth docs.
- [ ] Run focused GREEN and segment slice: `rtk pytest tests/instrument_registry tests/strategy_compiler tests/api tests/backtest_runner -q`.
- [ ] Reconcile `structure.md`, `findings.md`, and `handguard.md` with Segment 4 evidence.

## Master reconciliation

- [ ] Run `python3 -m compileall -q packages services tests`.
- [ ] Run `rtk pytest tests -q`.
- [ ] Run the Nautilus runtime pin check snippet from `handguard.md`.
- [ ] Run `cd apps/web && npm run typecheck && npm test -- --run && npm run build && npm run test:e2e`.
- [ ] Run `git diff --check`.
- [ ] Grep for forbidden authority drift in `packages/`, `services/`, and `apps/web`.
- [ ] Final-update `structure.md`, `findings.md`, and `handguard.md` with master reconciliation evidence.
