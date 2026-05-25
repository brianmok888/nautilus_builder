# Post-closure R2 findings implementation plan

**Date:** 2026-05-25  
**Repo:** `/home/mok/projects/nautilus_builder`  
**Mode:** Superpowers brainstorming/TDD with an autopilot-style segment loop (`plan -> implement/verify -> review/reconcile`).  
**Authority boundary:** Builder remains authoring/backtest/evidence-only; Daedalus/live execution is not edited or imported.

## Reference baseline

- NautilusTrader official docs: use `BacktestNode` with configuration objects for production-style high-level backtesting, and use `ParquetDataCatalog` for streaming catalog-backed backtests.
- NautilusTrader adapter docs/testing specs: adapter readiness requires DataTester/ExecTester evidence; Builder must not imply adapter/live readiness without those tests.
- LangGraph/LangChain advisory context: durable AI workflows depend on persistent thread/checkpoint/audit state and human-in-the-loop provenance; Builder should keep AI advisory-only and validate lineage IDs before apply.
- EvoMap/evolver remains advisory-context only; no runtime dependency is added.
- aiogram-dialog-menus is a negative-inventory lens only; no Telegram/aiogram runtime is in scope.

## Design approach options

1. **Strict-only hardening (recommended).** Keep compatibility/dev paths intact, but make production-facing FastAPI/helper strict paths fail closed with auth, root policy, scoped artifacts, provenance, and safe identifiers. This minimizes churn while closing the named risks.
2. **Global hard break.** Remove all non-strict compatibility paths. This would be simpler conceptually but would break existing fixture/dev tests and UI shells that intentionally use lightweight `ApiApp`.
3. **Facade rewrite.** Introduce a new API/service façade for all strict production paths. This adds indirection and scope risk without needing it for the current findings.

Chosen plan: option 1. Keep compatibility paths explicitly fixture/dev-only and improve labels so they cannot be confused with production evidence.

## Segments and TDD gates

### Segment 1 — Promotion evidence lineage binding

RED tests:
- strict promotion rejects missing scoped artifacts as typed `ValueError` / FastAPI 422, not `FileNotFoundError`;
- strict promotion rejects artifacts whose payload/metadata `compile_hash` differs from the request;
- strict promotion rejects artifacts whose lineage metadata (`strategy_version`, `strategy_version_id`, `result_id`, or `job_id` when present/required) contradicts the request.

GREEN implementation:
- `LocalJsonArtifactStore.get_json()` converts missing/corrupt/envelope errors to `ValueError`;
- `PromotionService` passes `compile_hash`/strategy version into evidence validation and verifies payload/metadata binding;
- route mapping stays 422/403.

### Segment 2 — Catalog traversal/root policy

RED tests:
- `_catalog_manifest()` rejects symlinked files and symlinked directories inside an allowed catalog;
- strict registry use without `catalog_root` rejects strict registration/selection;
- strict backtest job creation rejects an unrooted catalog registry.

GREEN implementation:
- manifest traversal lstat/resolve-checks every candidate before reading;
- `CatalogDatasetRegistryService` exposes `has_root_policy`/`require_root_policy()` and strict registration/selection flags;
- strict API job creation calls root-policy guard.

### Segment 3 — Tenant/project scoping outside backtest jobs

RED tests:
- strict FastAPI strategy create/list/detail/draft/version require bearer auth and ignore spoofed body scope;
- workflow result/suggestion/lineage reads deny cross-project access;
- runtime event replay and promotion-request routes require auth context in FastAPI.

GREEN implementation:
- repository records carry `user_id`/`project_id` where needed;
- package routes accept optional context/strict flags and use scoped read helpers;
- FastAPI derives `UserProjectContext` consistently for production-facing routes while lightweight `ApiApp` remains dev/fixture compatibility.

### Segment 4 — Storage identifiers and AI provenance/audit

RED tests:
- unsafe SQL schema/table/Redis namespace strings are rejected;
- blank AI apply provenance IDs are rejected;
- FastAPI AI apply uses an injected durable audit store rather than fresh per-request memory.

GREEN implementation:
- central safe identifier regex for Builder storage schemas/tables/namespaces;
- AI service validates non-empty provenance IDs;
- FastAPI accepts injected AI audit store/service and maps apply errors to 422.

### Segment 5 — Fixture artifact refs and frontend warning cleanup

RED tests/checks:
- production FastAPI workflow result fallback does not expose unscoped fixture artifact refs;
- compatibility fallback payloads are labeled fixture/dev evidence;
- frontend verification warnings are reduced by config/env cleanup where possible.

GREEN implementation:
- fallback dashboard payload includes `evidence_mode=fixture_dev_only` and production strict route requires auth/repository-owned result;
- result normalizer labels fixture refs explicitly;
- Playwright web server env unsets conflicting color vars; Vitest config migrated if safe.

## Segment reconciliation contract

After each segment:
1. rerun targeted tests and compile checks for touched packages;
2. append closure status/evidence to `structure.md`, `findings.md`, and `handguard.md`;
3. clean generated files;
4. only proceed once the segment is green.

## Master verification

```bash
python3 -m compileall -q packages services tests
rtk pytest tests -q
python3 - <<'PY'
from packages.backtest_runner.runtime_check import check_nautilus_runtime_version
status = check_nautilus_runtime_version()
print(status.message)
assert status.is_match, status.message
PY
cd apps/web && npm run typecheck && npm test -- --run && npm run build && npm run test:e2e
git diff --check
```

