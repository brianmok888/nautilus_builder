# Handguard — Production Safety Guards & Readiness Matrix

**Last Updated:** 2026-06-12
**Review:** Deep code review + NT alignment audit

---

## Active Guards

| # | Guard | Status | Enforced By | Tests |
|---|-------|--------|-------------|-------|
| 1 | Version consistency | ✅ ACTIVE | `packages/builder_metadata/version.py` canonical source; pyproject.toml, RELEASE.md, /health/build must agree | `test_version_consistency.py` |
| 2 | Readiness matrix v4 | ✅ ACTIVE | 10 required capabilities; `live_execution` = out_of_scope; `nd_runtime_changes` = out_of_scope | `test_production_config.py` |
| 3 | CI workflow structure | ✅ ACTIVE | ci.yml, security.yml, docker.yml exist with required jobs | `test_ci_workflows.py` |
| 4 | Changelog version alignment | ✅ ACTIVE | First CHANGELOG version matches pyproject.toml | `test_changelog_version_alignment.py` |
| 5 | Authority rules | ✅ ACTIVE | `authority_rules.py` blocks forbidden output modes and authority fields | `test_forbidden_execution_blocks.py` |
| 6 | Forbidden execution scan | ✅ ACTIVE | `scripts/check_forbidden_authority.sh` scans for `submit_order(`, `TradeAction(`, `execution_authority: true` | `test_repo_hygiene.py` |
| 7 | Production token validation | ✅ ACTIVE | `validate_production_token()` requires ≥32 chars, not dev tokens | `test_production_config.py` |
| 8 | CORS validation | ✅ ACTIVE | `validate_cors_config()` blocks wildcard origins in production | `test_production_config.py` |
| 9 | Evidence fail-closed | ✅ ACTIVE | Production/staging raises ValueError if evidence storage is in-memory | `fastapi_app.py` |
| 10 | Evidence project scoping | ✅ ACTIVE | Evidence routes require `project_id` from auth context; cross-project leakage blocked | `test_postgres_repository.py` |
| 11 | Schema family unification | ✅ ACTIVE | `parse_strategy_spec()` handles classic_v1 + microstructure_v1 | `test_schema_family_unification.py` |
| 12 | Microstructure execution authority | ✅ ACTIVE | `StrategySpecMicrostructureV1` enforces `execution_authority=False` at model level | `test_v2_validation.py` |
| 13 | Source health validation | ✅ ACTIVE | Microstructure specs validate source health records | `test_source_health.py` |
| 14 | Deterministic bundle hash | ✅ ACTIVE | `compile_strategy_spec_bundle` produces same hash for same input | `test_compile_bundle.py` |
| 15 | Bundle forbidden authority scan | ✅ ACTIVE | All generated artifacts scanned for authority violations | `test_bundle_authoritative.py` |
| 16 | Credential slot HTTP disabled | ✅ ACTIVE | Returns `credential_slot_http_disabled` with 410 status | `credentials.py` |
| 17 | Browser credential bootstrap disabled | ✅ ACTIVE | Returns error payload; UI has no `CredentialSlotBootstrap` component | handguard tests |
| 18 | Execution reconciliation ≥60min | ✅ ACTIVE | `ExecEngineConfig` enforces `reconciliation_lookback_mins >= 60` | `config_contract.py` |
| 19 | Risk engine bypass forbidden | ✅ ACTIVE | `bypass: Literal[False] = False` in `RiskEngineConfig` | `config_contract.py` |
| 20 | Strategy-lane decoupled | ✅ ACTIVE | `strategy_lane_coupled: Literal[False] = False` enforced in models | `models.py` |
| 21 | Paper strategy no-order contract | ✅ ACTIVE | `execution_authority=False`, `may_submit_order=False` enforced | `paper_strategy.py` |
| 22 | Docker image no local env files | ✅ ACTIVE | Docker tests verify no `.env.execution.local` in images | `test_dockerfile_safety.py` |
| 23 | API route auth coverage | ✅ ACTIVE | Runtime tests verify every `/api/*` route rejects missing tokens | `test_fastapi_app.py` |
| 24 | Audit middleware | ✅ ACTIVE | All API mutations logged with actor, project, resource | `fastapi_app.py` |
| 25 | Evidence migration v7 | ✅ ACTIVE | Creates `evidence_refs` table with project-scoped indexes | `test_postgres_repository.py` |

---

## NT Alignment Guards

| # | Guard | Status | Notes |
|---|-------|--------|-------|
| N1 | NT version pin (Builder) | ⚠️ MISMATCH RISK | pyproject.toml = 1.227.0, installed = 1.227.0 → OK but no upper bound pin |
| N2 | NT version pin (Daedalus) | 🔴 MISMATCH | pyproject.toml = 1.228.0, installed = 1.227.0 → MUST FIX |
| N3 | Lifecycle: super().__init__() first | ✅ VERIFIED | All strategies/actors call super first |
| N4 | Lifecycle: on_start fetches instrument with null check | ✅ VERIFIED | `paper_strategy.py` checks `if self.instrument is not None` |
| N5 | Lifecycle: request_bars before subscribe_bars | ⚠️ PARTIAL | Paper strategy subscribes directly to quote_ticks (no warmup) |
| N6 | Lifecycle: on_stop cancels/unsubscribes | ⚠️ PARTIAL | Paper strategy has no explicit on_stop |
| N7 | No blocking I/O in handlers | ✅ VERIFIED | No requests.get, file I/O, or time.sleep in handlers |
| N8 | StrategyConfig frozen=True | ✅ VERIFIED | `ExecutionLanePaperStrategyConfig(StrategyConfig, frozen=True)` |
| N9 | reconciliation=True enforced | ✅ VERIFIED | Literal True with ≥60min lookback |
| N10 | risk bypass=False enforced | ✅ VERIFIED | Literal[False] |
| N11 | Custom data typed via @customdataclass | N/A | Daedalus uses custom topic bus instead |
| N12 | Actors use publish_signal/publish_data | ⚠️ NOT COMPLIANT | Daedalus uses custom nt_actor_bus with string topics |
| N13 | LiveNode vs TradingNode label | ✅ VERIFIED | nautilus_runtime.py labels it `python_live_integration_specific` |

---

## Deprecated / Closed Items

| Item | Closed Since | Evidence |
|------|-------------|----------|
| Browser credential slot | v3 | Returns 410, UI component removed |
| Strategy-lane coupling | v3 | Literal[False] enforced at model + config level |
| Coinbase International adapter ref | N/A (never present) | No references found |
| dYdX v3 adapter ref | N/A (never present) | No references found |
| `fill_limit_at_touch` | N/A (not used) | No references found |

---

## Open Items Requiring Action

| Priority | Item | Owner | Target |
|----------|------|-------|--------|
| CRITICAL | Daedalus NT version pin mismatch (C-01) | Daedalus | Immediate |
| CRITICAL | Unbounded in-memory stores (C-02) | Builder | Before production |
| HIGH | Multi-venue adapter config builders (H-01) | Builder | Before multi-venue |
| HIGH | Custom message bus → NT native (H-02) | Daedalus | Migration plan |
| HIGH | TradeDecisionActor async re-entrancy (H-03) | Daedalus | Before live |
| HIGH | ExtendedExecutionClient reconciliation (H-04) | Daedalus | Before live |
| HIGH | Evidence fail-closed bypass path (H-05) | Builder | Before production |
| MEDIUM | Telegram signal UI test failures (M-05) | Daedalus | Next sprint |
| MEDIUM | Paper strategy bar subscription (M-01) | Builder | Next sprint |
| WATCH | Dual-repo contract synchronization (AW-01) | Both | Architecture review |
| WATCH | Custom bus → LiveNode migration (AW-02) | Daedalus | Architecture plan |
| WATCH | In-memory defaults for production (AW-03) | Builder | Production checklist |
