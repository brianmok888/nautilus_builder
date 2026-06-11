# Baseline Reworked Review — Gap Closure v2

**Review date:** 2026-06-11
**Branch:** feat/close-builder-gaps-v2
**Base commit:** 6bb5a93
**Base branch:** master

## Command results

### Compile check
```
python3 -m compileall -q packages services tests scripts
# PASS (0 errors)
```

### Test suite
```
python3 -m pytest tests/ -q --tb=line
# 1176 passed, 1 skipped
```

### Forbidden authority scan
```
bash scripts/check_forbidden_authority.sh
# PASSED
```

### Frontend typecheck
```
cd apps/web && npm run typecheck
# PASS
```

### Frontend tests
```
cd apps/web && npm test
# Test Files 33 passed, 1 skipped; Tests 131 passed, 4 skipped
```

### Frontend build
```
cd apps/web && npm run build
# PASS
```

## Current version values

| Source | Value |
|--------|-------|
| pyproject.toml | 0.1.0 |
| builder_metadata/version.py | reads from installed metadata or pyproject.toml |
| /health/build | uses get_canonical_version() |

## Pre-existing failures

None. All tests pass.

## Gap register — v2 remaining gaps mapped to segments

| Gap | Segment | Status in v1 | v2 Action Required |
|-----|---------|---------------|-------------------|
| Baseline audit register | 00 | Partial | Create this document |
| Version metadata has build_info model incomplete | 01 | Partial | Add BuilderBuildInfo model with git/build env |
| CI missing verify_all.sh, security scan needs expansion | 02 | Partial | Add verify_all.sh, expand scan, add allowlist |
| No readiness package/service/API endpoint | 03 | Partial (READINESS.md only) | Add packages/readiness/ with models, service, GET /readiness |
| StrategySpec v2 needs archetype fixtures, schema export test | 04 | Partial | Add archetype fixtures, schema export test |
| Validation needs structured issue codes, dependency graph validation | 05 | Partial | Add feature_registry, source_health, authority_rules |
| Compiler needs full deterministic artifact bundle with manifest | 06 | Partial | Add full manifest, all artifact files, hash reproducibility |
| Dataset catalog needs DuckDB index, alignment checks, real data path | 07 | Partial | Add DuckDB index, alignment, Parquet fixtures |
| Evidence needs API endpoints, storage backend | 08 | Partial | Add POST/GET /evidence, storage abstraction |
| Promotion needs state machine, evidence policy, blocking reasons | 09 | Partial | Add state machine, evidence_policy, blocking codes |
| API needs full route decomposition, OpenAPI snapshot, error standard | 10 | Partial | Add route files, OpenAPI snapshot, ApiError |
| Auth needs capabilities model, production fail-closed | 11 | Partial | Add capabilities, production checks, env files |
| Object storage abstraction missing | 12 | Not started | Add packages/object_storage/, packages/persistence/ |
| UX traceability components missing | 13 | Not started | Add traceability components |
| Audit/observability models need expansion | 14 | Partial | Add packages/audit/, metrics |
| Docs consistency check missing | 15 | Not started | Add check_docs_consistency.py, doc files |
| Final verification and release docs | 16 | Not started | Run final commands, create report |
