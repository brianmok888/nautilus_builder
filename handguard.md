# Nautilus Builder Handguard

**Review date:** 2026-05-29 (updated — full deep review v2)
**Purpose:** Runtime-enforced boundaries and hardguard constraints that must not be violated. These are invariants, not suggestions.

---

## 1. Authority boundary

Builder NEVER holds `submit_order` authority.

```python
# These must remain False in all production paths:
execution_authority = False
may_submit_order = False
live_trading_authority = False
advisory_only = True
```

Enforcement:
- `execution_lane/nautilus_runtime.py` — `Literal[False]` on `browser_credentials_allowed`, `credential_inputs_allowed`, `strategy_lane_coupled`
- `strategy_validation/policy.py` — `FORBIDDEN_REFERENCES` blocks `submit_order`, `modify_order`, `cancel_order`, `close_position`, `TradeAction`
- `strategy_validation/policy.py` — `RAW_CODE_PATTERNS` blocks `eval`, `exec`, `subprocess`, `socket`, `requests`
- `backtest_runner/config_builder.py` — raises `ValueError` if `credentials` passed to backtest config
- `compiler.py` — sets `execution_authority=False` for all profiles

Guard: Any PR that changes these to `True` or `Literal[True]` must be rejected.

## 2. Credential boundary

- `.env.execution.local` is gitignored and local-dev-only. **Never deploy with real credentials in this file.**
- Venue credentials use prefixed keys only: `BINANCE_API_KEY`, `BINANCE_API_SECRET`, etc.
- Bare key names like `API_KEY`, `SECRET`, `PASSWORD` are forbidden by `credentials.py`.
- `_SECRET_KEYS` set in `models.py` recursively rejects credential leakage in profiles, commands, and reports.
- Browser UI must never collect or persist exchange/API credentials.

Guard: Any PR that adds bare credential key names or removes gitignore entries must be rejected.

## 3. Reconciliation boundary

- `reconciliation_lookback_mins` must be ≥ 60 at the model level (enforced: `Field(ge=60)`).
- `reconciliation_startup_delay_secs` must not be reduced below 10.
- `open_check_lookback_mins` must not be reduced below 60.
- Reconciliation must remain enabled for all execution profiles.

Guard: Any PR that lowers these thresholds without explicit justification must be rejected.

## 4. Adapter resolution boundary

- Adapter resolution must be routed through `packages/adapter_registry/`, not hardcoded to Binance.
- New adapters must be registered in the adapter registry before execution lane profiles can reference them.
- `generic_client_config_builder` must raise a clear error when credentials are missing, not silently connect.

Guard: Any PR that hardcodes adapter configuration outside the registry must be rejected.

## 5. Worker isolation boundary

- Native runner must not be used from the API event loop — worker process only.
- `services/workers/` entrypoints own the runtime lifecycle.
- The API layer must never directly import or start `TradingNode`.

Guard: Any PR that imports `TradingNode` in `services/api/` must be rejected.

## 6. Promotion evidence boundary

- Default `allow_legacy_fixture_refs` to `False` in production paths.
- Require `strict_evidence=True` for all non-dev promotion requests.
- Never set gate compatibility by fiat.
- Never fabricate evidence refs that were not produced/stored.
- Final/production-candidate movement requires validation, backtest, no-lookahead, risk, gate-compatibility, runtime-boundary, and manual approval evidence.

Guard: Any PR that bypasses evidence requirements in production paths must be rejected.

## 7. Terminal/UX boundary

The normal terminal is not a shell.

Allowed commands: `help`, `status`, `show config`, `show validation`, `show metrics`, `tail logs`, `request cancel`

Forbidden: shell, package install, network tools, process/container control, environment dumps, secrets, exchange credentials, direct worker memory mutation.

Guard: Any PR that adds shell-like commands to the terminal must be rejected.

## 8. Model naming boundary

Do not name Pydantic models with `Test` prefix unless they are actual pytest test classes.

- `WorkflowJobRecord` (renamed from `TestJobRecord`)
- `WorkflowResultRecord` (renamed from `TestResultRecord`)

Guard: Add a linter/hook that flags Pydantic model classes starting with `Test`.

## 9. Verification gate before readiness claims

```bash
python3 -m compileall -q packages services tests
python3 -m pytest tests/ -q --tb=line        # Must pass: 442+
cd apps/web && npx tsc --noEmit               # Must be clean
cd apps/web && npx vitest run                 # Must pass: 44+ (4 skipped OK)
cd apps/web && npm run build                  # Must succeed
```

Playwright E2E required for frontend-readiness claims:
```bash
cd apps/web && npx playwright install chromium && npm run test:e2e
```

Guard: No readiness claim without fresh evidence from all commands above.

## 10. UI design boundary

- `DESIGN.md` is the current design source of truth.
- Preserve the three primary sections: Strategy Builder, Backtest Center, Execution Lane.
- Browser UI must not collect or persist exchange/API credentials.
- Navigation labels keep product vocabulary first; demo IDs remain route examples.

Guard: Any PR that changes the three-section structure or adds credential collection UI must be rejected.

## 11. DataTester/ExecTester boundary

Builder gates on evidence refs but does not produce DataTester/ExecTester evidence. This is by design:

- Builder produces compile artifacts, validation reports, and backtest results.
- Adapter test evidence comes from the adapter's own test suite or Daedalus.
- Builder's execution lane correctly requires these refs to be non-blank before allowing commands.
- Document this boundary explicitly in architecture docs.

Guard: Any PR that claims Builder produces DataTester/ExecTester evidence must be rejected.

## 12. AI provider boundary

- OpenAI-compatible provider uses `urllib.request` with configurable timeout — no third-party HTTP dependency.
- Provider endpoint is operator-configured via env vars (`OPENAI_API_KEY`, `OPENAI_BASE_URL`, `OPENAI_MODEL`).
- Never derive endpoint URL from model output.
- Always validate LLM output through `validate_strategy_spec()` before acceptance.
- No certificate pinning currently — acceptable for operator-configured endpoints but should be documented.

Guard: Any PR that adds third-party HTTP dependencies to the AI provider must be rejected.

## 13. Security scan gate

Must remain clean:
- No hardcoded secrets in production code
- No blocking I/O in hot paths
- No `submit_order`, `TradeAction`, `close_position` in builder-side code
- No `eval()`, `exec()`, `subprocess`, `os.system`, `time.sleep` in production code
- Credential keys are venue-prefixed and forbidden-key-filtered
- Artifact URIs are path-traversal-safe

Guard: Run AST scan as CI gate. Reject any PR that introduces forbidden patterns.

## 14. Catalog-backed replay reconciliation

- `catalog_backed_replay_smoke` must remain runnable with `CATALOG_BACKED_REPLAY_SMOKE_MODE` env variable support.
- synthetic historical quote ticks must exercise the full BacktestNode pipeline.
- This is a wiring and data-flow check — not full trading-production readiness.
- Master reconciliation — catalog-backed Nautilus replay evidence must appear in all three review docs (structure, findings, handguard).

## 15. NT version alignment gate

- Builder must track Daedalus's `nautilus_trader` version within 2 minor releases.
- Current: Builder=1.227.0, Daedalus=1.227.0 → **aligned** (H1 FIXED).
- Upgrade path: verify adapter config builder compatibility at each version step.
- Upgrade complete: 1.223.0 → 1.227.0, `testnet` → `environment` param, 442 tests passing.

## 16. Daedalus Telegram integration boundary

- Daedalus owns the aiogram-dialog Telegram gateway entirely.
- Builder has no Telegram dependency and must not add one.
- Strategy lifecycle events in Builder can be surfaced via Daedalus's signal delivery dialog, but only through Daedalus's `nautilus_runtime/live/telegram_gateway/` path.
- Builder → Daedalus notification contract: optional `notification_config` in execution profiles (not yet implemented).

Guard: Any PR that adds aiogram/aiogram-dialog dependencies to Builder must be rejected.

## 17. Fixture fallback gate (H2 fix)

- `workflow_result_payload` gates fixture fallback behind `BUILDER_ALLOW_FIXTURE_FALLBACK` env var.
- Default behavior (env var unset): returns 404 for `res_001` with no real data.
- Only returns fixture data when env var is explicitly `1`, `true`, or `yes`.
- Production must never set this env var.

Guard: Any PR that re-enables fixture fallback by default must be rejected.

## 18. Adapter credential enforcement (H3 fix)

- `generic_client_config_builder` raises `ValueError` when no venue-prefixed credentials are found.
- Silent empty-config connections are no longer possible.
- All adapters must provide `{VENUE}_*` prefixed credential keys with non-empty values.

Guard: Any PR that removes the `_require_non_blank_credentials` check must be rejected.

## 19. Runtime label extensibility (M3 fix)

- `runtime_label` is `str` with a validator accepting `python_live_integration_specific` and `rust_live_node`.
- New labels must be added to `_KNOWN_RUNTIME_LABELS` in `nautilus_runtime.py`.
- Default remains `python_live_integration_specific`.

Guard: Any PR that removes the validator or adds labels without updating the known set must be rejected.

## 20. Legacy/deprecation closure schedule

| Item | Deadline | Action |
|------|----------|--------|
| `storage_config.py` legacy alias | 2026-07-01 | Remove, add tracking issue |
| `backtest_jobs.py` legacy hash | 2026-07-01 | Remove, add tracking issue |
| `allow_legacy_fixture_refs` | 2026-07-01 | Add hard cutoff with env flag |
| `res_001` fixture fallback | 2026-07-01 | Default `allow_fixture_fallback=False` in production |
| `PostgresWorkflowRepository` alias | 2026-07-01 | Rename to SqliteWorkflowRepository |

Guard: After 2026-07-01, any PR that re-enables legacy paths without env flag must be rejected.

## 21. Production deployment gate (S5)

- `_register_env_dev_token` rejects known dev tokens (`dev-token`, `test-token`, `changeme`) when `APP_ENV=production`.
- Custom tokens work in all environments.
- `docker-compose.yml` uses `${POSTGRES_PASSWORD:-builder_dev}` for env var override.
- Postgres port bound to `127.0.0.1:5432:5432` (localhost only).
- Tests: `tests/api/test_production_safety.py` (5 tests).

Guard: Any PR that removes the `_UNSAFE_DEV_TOKENS` check or reverts port/password hardening must be rejected.

## 22. Onboarding boundary (S12-S18)

The repo must maintain the developer onboarding experience:

- `.env.example` must document all docker-compose and application env vars.
- `scripts/run_dev.sh` must start the development environment.
- `scripts/run_tests.sh` must run the verification gate.
- `DEVELOPMENT.md` must be the single source for onboarding instructions.
- `docs/examples/` must contain runnable demo scripts exercising the full pipeline.
- `doc/strategy_dev_guide.md` must document the strategy lifecycle.
- Adapter discovery must support drop-in registration via `@register_adapter`.
- `# @param` convention must be parseable by `packages/ai_builder/param_parser.py`.

Guard: Any PR that removes onboarding files, scripts, or demo examples without replacement must be rejected.

## 23. Docker zero-config boundary (S18)

`docker compose up -d` must start a working application:

- All services have health checks.
- API depends on postgres being healthy.
- Web depends on API being healthy.
- Postgres port bound to 127.0.0.1 only.
- `.env.example` covers all compose env vars.
- Demo strategies seeded on first startup.

Guard: Any PR that removes health checks or reverts port/password hardening must be rejected.

## 24. End-to-end pipeline boundary (S20-S22)

The `scripts/run_backtest.py` script chains all Builder seams into a single flow:

- Must accept `--spec <path>` pointing to a valid StrategySpec JSON file.
- Must validate, compile, and run backtest in sequence.
- Must always set `execution_authority=False`.
- Must support `--json` for machine-readable output.
- Must fail cleanly for invalid or missing spec files.
- Example spec files must exist in `docs/examples/specs/`.

Guard: Any PR that removes `scripts/run_backtest.py` or example spec files without replacement must be rejected.
