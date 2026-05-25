# Nautilus Builder 2026-05-25 Findings Closure Design

**Date:** 2026-05-25  
**Approved approach:** Segment-by-segment TDD/autopilot-style closure from the 2026-05-25 review findings.  
**Target repo:** `/home/mok/projects/nautilus_builder`  
**Reference repo:** `/home/mok/projects/Nautilus-Daedalus` is read-only.  
**Out of scope:** editing Nautilus-Daedalus, adding Builder live order authority, adding Telegram/aiogram runtime behavior, or adopting LangChain/LangGraph/EvoMap runtime dependencies.

## Goal

Close the 2026-05-25 HIGH/MEDIUM findings while preserving Builder as an authoring, validation, catalog-backed backtest, evidence, and shadow-promotion product. Builder must remain no-live-order: Daedalus owns live signal/gate/execution authority.

## Authoritative reference posture

- NautilusTrader upstream and docs are authoritative for catalog-backed `BacktestNode` replay, adapter testing, `DataTester`/`ExecTester`, and `LiveNode` vs legacy `TradingNode` terminology.
- The active NautilusTrader upstream `HEAD` checked during this pass is `d5d86b7f0d9bef3d72aada7010f4d35a1236a21c` on `develop`; Builder's local runtime remains pinned/checked separately.
- EvoMap/evolver, LangChain, and LangGraph are advisory ecosystem references only. Builder source must not gain direct runtime imports or advisory-to-execution coupling.
- The loaded `aiogram-dialog-menus` skill is a negative-inventory lens for this repo: no Telegram dialog surface is in scope.

## Architecture

The closure is split into four safe, testable segments plus master reconciliation:

1. **Catalog trust and real user-catalog replay** — split synthetic smoke from production/user replay, require configured catalog roots, fail closed on missing/empty/mismatched catalogs, and record read-only manifest evidence.
2. **Auth-derived API scope and validated job creation** — make strict API paths derive `UserProjectContext` from verified tokens, ignore spoofed client scope, and validate profile/dataset selection before job creation.
3. **Promotion evidence resolution** — require scoped Builder artifact refs for strict promotion readiness and verify scope, checksum, and artifact type through the artifact store.
4. **Registry/replay semantic alignment** — expose `quote_ticks` consistently for StrategySpec replay and rename no-order backtest compiler output away from order-intent wording.

## Component design

### Segment 1 — catalog trust and replay provenance

- `packages/catalog_datasets/service.py` owns registry-time catalog path trust through a `CatalogPathPolicy` with a configured root.
- `packages/backtest_runner/strategy_spec_replay.py` owns two explicit modes:
  - `strategy_spec_synthetic_catalog_smoke` writes deterministic test-kit data into a controlled temp/rooted catalog and labels evidence as `synthetic_test_kit`.
  - `strategy_spec_catalog_replay` reads an existing user catalog only, requires `catalog_root`, and labels evidence as `user_catalog`.
- User replay must not call Nautilus `TestDataStubs` or write new rows. It counts matching pre-existing quote ticks before replay and records a manifest checksum/file count.
- Worker strategy-spec replay requires a safe catalog root and passes it to the replay function.

### Segment 2 — API scope and job validation

- `packages/auth/service.py` stays the token verification seam.
- `services/api/routes/backtest_jobs.py` accepts a trusted context from the API layer. Strict mode returns 401 without context and ignores `user_id`/`project_id` in request bodies or queries.
- Backtest job creation validates adapter/instrument/data type/timeframe/market/date range through `InstrumentRegistryService` and validates dataset selection through `CatalogDatasetRegistryService` before writing a job.
- The lightweight `ApiApp` may keep explicit dev/test compatibility only when opted into `allow_client_scope=True`; strict FastAPI wiring must use auth-derived context.

### Segment 3 — promotion evidence artifacts

- `packages/promotions/service.py` resolves `PromotionEvidenceRefs` against `LocalJsonArtifactStore` in strict mode.
- Each evidence key must map to a scoped `artifact://builder/{project_id}/{user_id}/{artifact_type}/{artifact_id}` ref whose `artifact_type` matches the evidence key.
- The artifact store already verifies checksum and scope on read; promotion captures evidence checksums in the returned request model.
- Legacy unscoped refs are allowed only through an explicit fixture/dev flag.

### Segment 4 — replay data type and output semantics

- `packages/instrument_registry/service.py` makes `quote_ticks` visible and validated for `BTCUSDT-PERP` because StrategySpec replay consumes quote ticks.
- A contract test asserts the StrategySpec replay data type is present in registry availability.
- `packages/strategy_compiler/compiler.py` renames the backtest compile `output_mode` to `backtest_signal_observation` and docs/tests stop using `BacktestOrderIntent` for Builder no-order artifacts.

## Error handling

- Missing catalog root: `ValueError("catalog_root is required ...")`.
- Out-of-root/symlink catalog path: `ValueError("catalog path outside configured root")` or `ValueError("catalog path must not traverse symlinks")`.
- Missing/empty user catalog: `ValueError("user catalog has no matching quote_ticks")`.
- Strict API missing/invalid token: 401 with `auth_required` or `invalid_auth_token`.
- Strict API profile/dataset mismatch: 422 with deterministic error text.
- Strict promotion legacy/missing/wrong-scope refs: 422 at route boundaries or `ValueError` in package tests.

## Testing strategy

Every segment follows TDD: write failing tests, run focused RED, implement minimal code, run focused GREEN, run a segment slice, then update `structure.md`, `findings.md`, and `handguard.md` with reconciliation evidence.

Master reconciliation runs:

```bash
python3 -m compileall -q packages services tests
rtk pytest tests -q
python3 - <<'PY'
from packages.backtest_runner.runtime_check import check_nautilus_runtime_version
status = check_nautilus_runtime_version()
assert status.is_match, status.message
PY
cd apps/web && npm run typecheck && npm test -- --run && npm run build && npm run test:e2e
git diff --check
```

## Acceptance criteria

- User-catalog StrategySpec replay consumes only pre-existing catalog data under an allowed root and records provenance/manifest evidence.
- Synthetic StrategySpec smoke remains available but cannot be confused with user-catalog ingestion evidence.
- Strict API job creation derives user/project scope from auth, ignores spoofed body/query scope, and validates profile/dataset before job creation.
- Promotion evidence refs are scoped, resolved, checksum-verified, and type-checked in strict mode.
- Market catalog and StrategySpec replay agree on `quote_ticks`.
- No Builder artifact uses `backtest_order_intent` or `BacktestOrderIntent` for the no-order replay path.
