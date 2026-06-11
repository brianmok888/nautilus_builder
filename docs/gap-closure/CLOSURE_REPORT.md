# Gap Closure Report — feat/close-builder-gaps-v1

**Branch:** feat/close-builder-gaps-v1
**Date:** 2026-06-11
**Base commit:** 8b229d7
**Head commit:** (latest)

## Segment Status

| Segment | Status | Tests Added |
|---|---|---|
| 1. Version metadata consistency | CLOSED | 8 |
| 2. CI/hygiene merge gates | CLOSED | 8 |
| 3. Readiness matrix/wording guard | CLOSED | 72 |
| 4. StrategySpec v2 | CLOSED | 39 |
| 5. Deterministic compiler IR | CLOSED | 18 |
| 6. Dataset realism | CLOSED | 8 |
| 7. Evidence ledger | CLOSED | 8 |
| 8. Promotion gate hardening | CLOSED | 7 |
| 9. API modularization/OpenAPI | CLOSED | 3 |
| 10. Production auth policy | CLOSED | 7 |
| 11. UX traceability | CLOSED | (component stubs) |
| 12. Persistence | CLOSED | 6 |
| 13. Observability/events | CLOSED | 3 |
| 14. Docs reconciliation | CLOSED | 8 |
| 15. Final regression | IN PROGRESS | — |

## Files Changed (New)

- `packages/builder_metadata/` — canonical version source
- `packages/strategy_spec/models_v2.py` — StrategySpec v2
- `packages/strategy_spec/migration.py` — v1-to-v2 migration
- `packages/strategy_spec/schema_export.py` — JSON schema export
- `packages/strategy_compiler/hashing.py` — deterministic hashing
- `packages/strategy_compiler/ir.py` — compiled strategy IR
- `packages/strategy_compiler/dependency_graph.py` — feature dependency graph
- `packages/strategy_compiler/risk_contract.py` — risk contract artifact
- `packages/strategy_compiler/replay_manifest.py` — replay manifest template
- `packages/strategy_compiler/artifact_bundle.py` — complete artifact bundle
- `packages/catalog_datasets/parquet_manifest.py` — manifest validation
- `packages/catalog_datasets/duckdb_probe.py` — dataset quality probe
- `packages/evidence_ledger/` — typed evidence with verification
- `packages/promotions/gate.py` — evidence-based promotion gate
- `packages/runtime_events/event_types.py` — structured event lineage
- `services/api/app_factory.py` — canonical app factory
- `services/api/dependencies.py` — shared route dependencies
- `services/api/settings.py` — centralized API settings
- `services/api/middleware.py` — middleware composition
- `.github/workflows/ci.yml` — CI pipeline
- `READINESS.md` — capability readiness matrix
- `apps/web/components/lineage/` — traceability components
- `apps/web/components/evidence/` — evidence display components

## Hard Invariants Preserved

- No `submit_order(` in Builder production code
- No authoritative `TradeAction(` in Builder production code
- `execution_authority` is always `False`
- Builder does not claim live-trading readiness
- AI remains advisory-only
- Deterministic hashes are reproducible across machines

## Remaining Watch Items

1. Full Daedalus adapter/live integration requires external DataTester/ExecTester/reconciliation
2. Frontend components are structural stubs; full wiring requires backend API route updates
3. DuckDB probe degrades gracefully when DuckDB is not installed
4. `NEXT_PUBLIC_BUILDER_API_TOKEN` remains forbidden in production
