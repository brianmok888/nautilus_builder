# Handguard — Production Safety Guards & Readiness Matrix

**Last Updated:** 2026-06-12
**Scope:** nautilus_builder only
**Test Evidence:** 1512 passed, 1 skipped (2 pre-existing failures)

---

## Active Guards

| # | Guard | Status | Enforced By | Tests |
|---|-------|--------|-------------|-------|
| 1 | Version consistency | ✅ ACTIVE | `packages/builder_metadata/version.py` canonical source | `test_version_consistency.py` |
| 2 | Readiness matrix v4 | ✅ ACTIVE | 10 required capabilities | `test_production_config.py` |
| 3 | CI workflow structure | ✅ ACTIVE | ci.yml, security.yml, docker.yml | `test_ci_workflows.py` |
| 4 | Changelog version alignment | ✅ ACTIVE | CHANGELOG matches pyproject | `test_changelog_version_alignment.py` |
| 5 | Authority rules | ✅ ACTIVE | `authority_rules.py` blocks forbidden modes | `test_forbidden_execution_blocks.py` |
| 6 | Forbidden execution scan | ✅ ACTIVE | `check_forbidden_authority.sh` | `test_repo_hygiene.py` |
| 7 | Production token validation | ✅ ACTIVE | ≥32 chars, not dev tokens | `test_production_config.py` |
| 8 | CORS validation | ✅ ACTIVE | Blocks wildcard in production | `test_production_config.py` |
| 9 | Evidence fail-closed (factory) | ✅ ACTIVE | ValueError if in-memory in production | `test_evidence_startup_guard.py` |
| 10 | Evidence fail-closed (startup) | ✅ ACTIVE | Startup event re-validation | `test_evidence_startup_guard.py` |
| 11 | Evidence project scoping | ✅ ACTIVE | project_id from auth context | `test_postgres_repository.py` |
| 12 | Schema family unification | ✅ ACTIVE | classic_v1 + microstructure_v1 | `test_schema_family_unification.py` |
| 13 | Microstructure execution authority | ✅ ACTIVE | `execution_authority=False` | `test_v2_validation.py` |
| 14 | StrategySpec output_mode guard | ✅ ACTIVE | `enforce_signal_preview_only` validator | `test_output_mode_enforcement.py` |
| 15 | Source health validation | ✅ ACTIVE | Microstructure source health | `test_source_health.py` |
| 16 | Deterministic bundle hash | ✅ ACTIVE | Same input → same hash | `test_compile_bundle.py` |
| 17 | Bundle forbidden authority scan | ✅ ACTIVE | Scans for authority violations | `test_bundle_authoritative.py` |
| 18 | Credential slot HTTP disabled | ✅ ACTIVE | Returns 410 | `credentials.py` |
| 19 | Browser credential bootstrap disabled | ✅ ACTIVE | Returns error payload | handguard tests |
| 20 | Execution reconciliation ≥60min | ✅ ACTIVE | `reconciliation_lookback_mins >= 60` | `config_contract.py` |
| 21 | Risk engine bypass forbidden | ✅ ACTIVE | `Literal[False]` | `config_contract.py` |
| 22 | Strategy-lane decoupled | ✅ ACTIVE | `Literal[False]` | `models.py` |
| 23 | Paper strategy no-order contract | ✅ ACTIVE | `execution_authority=False`, `may_submit_order=False` | `paper_strategy.py` |
| 24 | Paper strategy lifecycle | ✅ ACTIVE | on_start, on_stop, on_reset | `test_paper_strategy_lifecycle.py` |
| 25 | Docker image no local env files | ✅ ACTIVE | Docker tests | `test_dockerfile_safety.py` |
| 26 | API route auth coverage | ✅ ACTIVE | Every /api/* route rejects missing tokens | `test_fastapi_app.py` |
| 27 | Audit middleware | ✅ ACTIVE | All mutations logged | `fastapi_app.py` |
| 28 | Evidence migration v7 | ✅ ACTIVE | evidence_refs with project indexes | `test_postgres_repository.py` |
| 29 | Auth token TTL + LRU eviction | ✅ ACTIVE | Configurable max_tokens + ttl_seconds | `test_token_eviction.py` |
| 30 | Execution lane bounded stores | ✅ ACTIVE | max_reports + max_sessions | `test_bounded_stores.py` |
| 31 | Multi-venue adapter fallback | ✅ ACTIVE | Generic builder for any venue | `test_multi_venue_config.py` |
| 32 | Credential file permissions | ✅ ACTIVE | chmod 0600 on write | `credentials.py` |
| 33 | SQL parameterization | ✅ ACTIVE | Parameterized LIMIT/OFFSET | `postgres_repository.py` |

---

## NT Alignment Guards

| # | Guard | Status |
|---|-------|--------|
| N1 | NT version pin matches installed | ✅ 1.227.0 |
| N2 | super().__init__() first | ✅ VERIFIED |
| N3 | on_start instrument null check | ✅ VERIFIED |
| N4 | request_bars before subscribe_bars | ✅ VERIFIED |
| N5 | on_stop explicit unsubscribe | ✅ VERIFIED |
| N6 | on_reset cleanup | ✅ VERIFIED |
| N7 | No blocking I/O in handlers | ✅ VERIFIED |
| N8 | StrategyConfig frozen=True | ✅ VERIFIED |
| N9 | reconciliation=True enforced | ✅ VERIFIED |
| N10 | risk bypass=False enforced | ✅ VERIFIED |
| N11 | LiveNode vs TradingNode label | ✅ VERIFIED |
| N12 | Multi-venue adapter support | ✅ VERIFIED |

---

## All Findings Closed

| ID | Finding | Status |
|----|---------|--------|
| C-01 | Unbounded in-memory stores | ✅ FIXED |
| H-01 | Multi-venue adapter configs | ✅ CONFIRMED (fallback exists) |
| H-02 | Evidence fail-closed bypass | ✅ FIXED (startup guard) |
| M-01 | Paper strategy bar subscription | ✅ FIXED |
| M-02 | Paper strategy on_reset | ✅ FIXED |
| M-03 | SQL LIMIT/OFFSET interpolation | ✅ FIXED |
| M-04 | StrategySpec output_mode | ✅ FIXED |
| L-01 | _installed_nautilus_version | ✅ FALSE POSITIVE |
| L-03 | Missing on_stop | ✅ FIXED |
| L-04 | Credential file permissions | ✅ FALSE POSITIVE |
