# Nautilus Builder Handguard

**Purpose:** concise guardrails for future Nautilus Builder work after the 2026-05-28 deep review.

## 1. Target and authority guard

- Work only in `/home/mok/projects/nautilus_builder` unless the user explicitly changes target.
- `/home/mok/projects/Nautilus-Daedalus` is a read-only alignment reference. Do not edit it from Builder sessions.
- Builder is contract/authoring/backtest/shadow-request software.
- Builder must never create `TradeAction` or call `submit_order`.
- Live order authority remains external: Daedalus gate + execution lane only.

## 2. Official NautilusTrader source guard

When Builder behavior depends on NautilusTrader semantics, use official sources first:

- https://github.com/nautechsystems/nautilus_trader
- https://nautilustrader.io/docs/latest/developer_guide
- https://nautilustrader.io/docs/latest/developer_guide/adapters/
- https://nautilustrader.io/docs/latest/developer_guide/spec_exec_testing/
- https://nautilustrader.io/docs/latest/concepts/backtesting/
- https://nautilustrader.io/docs/latest/concepts/live/

Current pinned version: `nautilus_trader==1.223.0`. Do not claim NautilusTrader readiness for versions beyond this pin without explicit upgrade testing.

## 3. NautilusTrader version alignment guard

- `BacktestVenueConfig.trade_execution` must be explicitly set in `config_builder.py` — never rely on defaults.
- Add a version-alignment test that fails on major/minor version drift from the pin.
- Plan v1.224+ upgrade covering: `fill_limit_inside_spread` rename, Coinbase IntX removal, `InstrumentProvider.load_all_async` default change, `trade_execution` default change.

## 4. AI draft acceptance guard

Before any AI draft is marked accepted or applied:

1. Validate provider output against `StrategySpec` via `validate_strategy_spec()`.
2. Run hard-rule validation over the full nested payload.
3. Reject every forbidden token from `doc/nautilus_builder_hardguards.md`.
4. Store validation errors in the AI audit record.
5. Keep status as draft/unvalidated unless validation evidence exists.

Minimum regression cases:

- nested `TradeAction`
- nested `submit_order`
- `api_key`, `secret_key`, `credential`
- `broker_order`, `exchange_order`
- missing StrategySpec required fields
- missing risk block
- unsupported output mode

## 5. StrategySpec validation guard

The executable schema and `doc/nautilus_builder_hardguards.md` must agree.

- If docs list an allowed v1 indicator/operator, schema/tests must accept it.
- If schema intentionally supports only an MVP subset, docs/UI must say so explicitly.
- Unknown fields remain forbidden unless schema versioning explicitly permits them.
- Forbidden terms must be checked recursively across keys and values (current `_walk_strings` does this correctly).

## 6. Frontend/backend DTO guard

Any frontend form that calls the backend must be tested against the real backend payload shape.

For market/backtest profile validation, the current backend requires:

```text
adapter_id
instrument_id
data_type
timeframe
market_type
date_range
```

Add at least one contract test that proves UI-submitted payloads succeed against `services.api.app.create_app()` or FastAPI/OpenAPI-derived schemas.

## 7. Execution lane guard

- `NautilusTradingNodeRuntimePlan` must keep: `browser_credentials_allowed=Literal[False]`, `credential_inputs_allowed=Literal[False]`, `strategy_lane_coupled=Literal[False]`.
- Credential slots must use venue-prefixed env keys only. No bare `API_KEY` or `SECRET` keys.
- `.env.execution.local` is gitignored and local-dev-only. Do not deploy with real credentials in this file.
- `reconciliation_lookback_mins` must be >= 60 at the model level, not just clamped in the config builder.
- Adapter resolution should be routed through `packages/adapter_registry/`, not hardcoded to Binance.

## 8. Promotion guard

Promotion requests must stay evidence-backed and non-authoritative.

- Default `allow_legacy_fixture_refs` to `False` in production paths.
- Require `strict_evidence=True` for all non-dev promotion requests.
- Never set gate compatibility by fiat.
- Never fabricate evidence refs that were not produced/stored.
- Final/production-candidate movement requires validation, backtest, no-lookahead, risk, gate-compatibility, runtime-boundary, and manual approval evidence.

## 9. Terminal/UX guard

The normal terminal is not a shell.

Allowed commands remain observational:

```text
help
status
show config
show validation
show metrics
tail logs
request cancel
```

Forbidden command classes include shell, package install, network tools, process/container control, environment dumps, secrets, exchange credentials, and direct worker memory mutation.

## 10. Model naming guard

Do not name Pydantic models with `Test` prefix unless they are actual pytest test classes.

- Rename `TestJobRecord` → `WorkflowJobRecord` or similar.
- Rename `TestResultRecord` → `WorkflowResultRecord` or similar.
- Add a linter/hook that flags Pydantic model classes starting with `Test`.

## 11. Verification gate before readiness claims

Run and record:

```bash
python3 -m compileall -q packages services tests
python3 -m pytest tests/ -q --tb=line
cd apps/web && npm run typecheck && npm test && npm run build
```

Playwright E2E is required for frontend-readiness claims. Install browsers first:

```bash
cd apps/web && npx playwright install chromium && npm run test:e2e
```

## 12. UI design guard

- Treat `DESIGN.md` as the current design source of truth before changing UI/UX/frontend structure.
- Preserve the three primary sections: Strategy Builder, Backtest Center, Execution Lane.
- Browser UI must not collect or persist exchange/API credentials.
- Navigation labels should keep product vocabulary first; demo IDs remain route examples.

## 13. DataTester/ExecTester boundary guard

Builder gates on evidence refs but does not produce DataTester/ExecTester evidence. This is by design:

- Builder produces compile artifacts, validation reports, and backtest results.
- Adapter test evidence (DataTester/ExecTester/reconciliation) comes from the adapter's own test suite or Daedalus.
- Builder's execution lane correctly requires these refs to be non-blank before allowing commands.
- Document this boundary explicitly in architecture docs.

## Catalog-backed replay reconciliation guard

- `catalog_backed_replay_smoke` must remain runnable with `CATALOG_BACKED_REPLAY_SMOKE_MODE` env variable support.
- synthetic historical quote ticks must exercise the full BacktestNode pipeline.
- This is a wiring and data-flow check — not full trading-production readiness.
- Master reconciliation — catalog-backed Nautilus replay evidence must appear in all three review docs (structure, findings, handguard).
