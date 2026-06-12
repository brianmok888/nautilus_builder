# Handguard — Production Safety Guards & Readiness Matrix

**Last Updated:** 2026-06-12
**Scope:** nautilus_builder only

---

## Active Guards

| # | Guard | Status | Enforced By | Tests |
|---|-------|--------|-------------|-------|
| 1 | Version consistency | ✅ ACTIVE | `packages/builder_metadata/version.py` canonical source | `test_version_consistency.py` |
| 2 | Readiness matrix v4 | ✅ ACTIVE | 10 required capabilities; `live_execution` = out_of_scope | `test_production_config.py` |
| 3 | CI workflow structure | ✅ ACTIVE | ci.yml, security.yml, docker.yml exist with required jobs | `test_ci_workflows.py` |
| 4 | Changelog version alignment | ✅ ACTIVE | First CHANGELOG version matches pyproject.toml | `test_changelog_version_alignment.py` |
| 5 | Authority rules | ✅ ACTIVE | `authority_rules.py` blocks forbidden output modes | `test_forbidden_execution_blocks.py` |
| 6 | Forbidden execution scan | ✅ ACTIVE | `check_forbidden_authority.sh` scans for `submit_order(`, `TradeAction(` | `test_repo_hygiene.py` |
| 7 | Production token validation | ✅ ACTIVE | `validate_production_token()` requires ≥32 chars | `test_production_config.py` |
| 8 | CORS validation | ✅ ACTIVE | `validate_cors_config()` blocks wildcard origins in production | `test_production_config.py` |
| 9 | Evidence fail-closed | ✅ ACTIVE | Production/staging raises ValueError if evidence is in-memory | `fastapi_app.py` |
| 10 | Evidence project scoping | ✅ ACTIVE | Evidence routes require `project_id` from auth context | `test_postgres_repository.py` |
| 11 | Schema family unification | ✅ ACTIVE | `parse_strategy_spec()` handles classic_v1 + microstructure_v1 | `test_schema_family_unification.py` |
| 12 | Microstructure execution authority | ✅ ACTIVE | `StrategySpecMicrostructureV1` enforces `execution_authority=False` | `test_v2_validation.py` |
| 13 | Source health validation | ✅ ACTIVE | Microstructure specs validate source health records | `test_source_health.py` |
| 14 | Deterministic bundle hash | ✅ ACTIVE | `compile_strategy_spec_bundle` same hash for same input | `test_compile_bundle.py` |
| 15 | Bundle forbidden authority scan | ✅ ACTIVE | All generated artifacts scanned for authority violations | `test_bundle_authoritative.py` |
| 16 | Credential slot HTTP disabled | ✅ ACTIVE | Returns `credential_slot_http_disabled` with 410 status | `credentials.py` |
| 17 | Browser credential bootstrap disabled | ✅ ACTIVE | Returns error payload; no `CredentialSlotBootstrap` component | handguard tests |
| 18 | Execution reconciliation ≥60min | ✅ ACTIVE | `ExecEngineConfig` enforces `reconciliation_lookback_mins >= 60` | `config_contract.py` |
| 19 | Risk engine bypass forbidden | ✅ ACTIVE | `bypass: Literal[False] = False` in `RiskEngineConfig` | `config_contract.py` |
| 20 | Strategy-lane decoupled | ✅ ACTIVE | `strategy_lane_coupled: Literal[False] = False` | `models.py` |
| 21 | Paper strategy no-order contract | ✅ ACTIVE | `execution_authority=False`, `may_submit_order=False` | `paper_strategy.py` |
| 22 | Docker image no local env files | ✅ ACTIVE | Docker tests verify no `.env.execution.local` in images | `test_dockerfile_safety.py` |
| 23 | API route auth coverage | ✅ ACTIVE | Runtime tests verify every `/api/*` route rejects missing tokens | `test_fastapi_app.py` |
| 24 | Audit middleware | ✅ ACTIVE | All API mutations logged with actor, project, resource | `fastapi_app.py` |
| 25 | Evidence migration v7 | ✅ ACTIVE | Creates `evidence_refs` with project-scoped indexes | `test_postgres_repository.py` |

---

## NT Alignment Guards

| # | Guard | Status | Notes |
|---|-------|--------|-------|
| N1 | NT version pin matches installed | ✅ OK | pyproject 1.227.0 = installed 1.227.0 |
| N2 | Lifecycle: super().__init__() first | ✅ VERIFIED | All strategies call super first |
| N3 | Lifecycle: on_start instrument null check | ✅ VERIFIED | `paper_strategy.py` checks `if not None` |
| N4 | Lifecycle: request_bars before subscribe_bars | ⚠️ PARTIAL | Subscribes directly to quote_ticks, no warmup |
| N5 | Lifecycle: on_stop cancels/unsubscribes | ⚠️ PARTIAL | No explicit on_stop |
| N6 | No blocking I/O in handlers | ✅ VERIFIED | No requests.get, file I/O, or time.sleep |
| N7 | StrategyConfig frozen=True | ✅ VERIFIED | `ExecutionLanePaperStrategyConfig(StrategyConfig, frozen=True)` |
| N8 | reconciliation=True enforced | ✅ VERIFIED | Literal True with ≥60min lookback |
| N9 | risk bypass=False enforced | ✅ VERIFIED | Literal[False] |
| N10 | LiveNode vs TradingNode label | ✅ VERIFIED | `python_live_integration_specific` label present |

---

## Deprecated / Closed Items

| Item | Closed Since | Evidence |
|------|-------------|----------|
| Browser credential slot | v3 | Returns 410, UI component removed |
| Strategy-lane coupling | v3 | Literal[False] at model + config level |
| Coinbase International adapter ref | N/A | Never referenced |
| dYdX v3 adapter ref | N/A | Never referenced |
| `fill_limit_at_touch` | N/A | Not used |

---

## Open Items Requiring Action

| Priority | Item | Target |
|----------|------|--------|
| CRITICAL | Unbounded in-memory stores (C-01) | Before production |
| HIGH | Multi-venue adapter config builders (H-01) | Before multi-venue |
| HIGH | Evidence fail-closed bypass path (H-02) | Before production |
| MEDIUM | Paper strategy bar subscription (M-01) | Next sprint |
| MEDIUM | Paper strategy on_reset/on_stop (M-02/L-03) | Next sprint |
| MEDIUM | SQL LIMIT/OFFSET parameterization (M-03) | Next sprint |
| WATCH | In-memory defaults for production (AW-01) | Production checklist |
| WATCH | Paper strategy warmup data (AW-02) | Architecture review |
