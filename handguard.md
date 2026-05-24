# Nautilus Builder Handguard

**Purpose:** concise guardrails for future Nautilus Builder work after the 2026-05-24 deep review.

## 1. Target and authority guard

- Work only in `/home/mok/projects/nautilus_builder` unless the user explicitly changes target.
- Do not edit `/home/mok/projects/Nautilus-Daedalus` from Builder review/work sessions.
- Builder is contract/authoring/backtest/shadow-request software.
- Builder must never create `TradeAction` or call `submit_order`.
- Live order authority remains external: Daedalus gate + execution lane only.

## 2. Official NautilusTrader source guard

When Builder behavior depends on NautilusTrader semantics, use official sources first:

- <https://github.com/nautechsystems/nautilus_trader>
- <https://nautilustrader.io/docs/latest/developer_guide>
- <https://nautilustrader.io/docs/latest/developer_guide/adapters/>
- <https://nautilustrader.io/docs/latest/developer_guide/spec_data_testing/>
- <https://nautilustrader.io/docs/latest/developer_guide/spec_exec_testing/>
- <https://nautilustrader.io/docs/latest/concepts/backtesting/>
- <https://nautilustrader.io/docs/latest/concepts/live/>

Do not claim NautilusTrader backtest/live readiness until a pinned `nautilus_trader` dependency and at least one concrete Nautilus engine smoke path exist.

## 3. AI draft acceptance guard

Before any AI draft is marked accepted or applied:

1. Validate provider output against `StrategySpec`.
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

## 4. StrategySpec validation guard

The executable schema and `doc/nautilus_builder_hardguards.md` must agree.

- If docs list an allowed v1 indicator/operator, schema/tests must accept it.
- If schema intentionally supports only an MVP subset, docs/UI must say so explicitly.
- Unknown fields remain forbidden unless schema versioning explicitly permits them.
- Forbidden terms must be checked recursively across keys and values.

## 5. Frontend/backend DTO guard

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

Do not rely only on mocked frontend tests. Add at least one contract test that proves UI-submitted payloads succeed against `services.api.app.create_app()` or FastAPI/OpenAPI-derived schemas.

## 6. Job/runtime audit guard

Every long-running backend-owned job should carry:

```text
job_id
status/stage
created_by
created_at
updated_at
strategy_spec_version_id
adapter_profile_id
instrument_id
data_range
worker_id
result_artifact_refs
event_stream_id
```

Every runtime event should carry:

```text
event_id
job_id
actor_type
actor_id
stage
level
message
timestamp
metadata
```

Use one canonical lifecycle vocabulary. If the docs say `SUCCEEDED`, code/tests should not silently use `COMPLETED`.

## 7. Promotion guard

Promotion requests must stay evidence-backed and non-authoritative.

- User-facing promotion route should request shadow/signal-preview only.
- Never set gate compatibility by fiat.
- Never fabricate evidence refs that were not produced/stored.
- Final/production-candidate movement requires validation, backtest, no-lookahead, risk, gate-compatibility, runtime-boundary, and manual approval evidence.

## 8. Terminal/UX guard

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

## 9. Verification gate before readiness claims

Run and record:

```bash
python3 -m compileall -q packages services tests
rtk pytest tests/strategy_spec tests/strategy_validation tests/adapter_registry tests/instrument_registry tests/strategy_compiler tests/backtest_jobs tests/runtime_events tests/backtest_runner tests/lifecycle tests/strategy_registry tests/promotions tests/web tests/ai_builder tests/integration tests/workflow_spine tests/auth tests/api -q
cd apps/web && npm run typecheck && npm test && npm run build
```

Playwright E2E is required for frontend-readiness claims, but this environment currently needs browser installation first:

```bash
cd apps/web && npx playwright install chromium
cd apps/web && npm run test:e2e
```

Do not mark frontend operator readiness complete until Playwright passes in a provisioned environment.

## 10. Stop condition for future reviews

A future review may move from **REQUEST CHANGES** to **COMMENT/APPROVE** only after:

- AI drafts cannot bypass schema or hard-rule validation.
- Forbidden token policy covers the hardguard list.
- Real UI market-profile validation succeeds against the backend contract.
- Job and event models satisfy hardguard audit fields.
- NautilusTrader dependency/version and at least one concrete backtest smoke are present, or docs clearly state fixture-only status.
- Playwright E2E is runnable and passing in CI/local documented setup.

## Segment 1 completion guard — validation hardening

Segment 1 is complete. Preserve these rules going forward:

- Do not mark AI provider output `accepted=True` unless recursive `validate_strategy_spec()` passes.
- Keep hardguarded credential/order terms in `FORBIDDEN_REFERENCES`.
- Add a regression test whenever `doc/nautilus_builder_hardguards.md` gains a new forbidden StrategySpec token.
- Default provider examples must stay full StrategySpec-shaped drafts, not simplified ad-hoc dictionaries.

Segment 1 evidence:

```bash
rtk pytest tests/strategy_validation tests/ai_builder tests/strategy_spec -q
# Pytest: 26 passed
```

## Segment 2 completion guard — market-profile DTO alignment

Segment 2 is complete. Preserve these rules going forward:

- Frontend market-profile validation payloads must include `adapter_id`, `instrument_id`, `data_type`, `timeframe`, `market_type`, and a backend-formatted `date_range` string.
- Do not reintroduce `adapter_profile_id` as the frontend's validation success contract unless the backend intentionally exposes it again with tests.
- Adapter UI labels must not depend on a non-existent backend `name` field.
- Instrument availability UI must consume backend `supported_data_types`, `supported_timeframes`, and string `available_date_ranges`.
- Keep at least one `services.api.app.create_app()` test proving the frontend payload shape validates.

Segment 2 evidence:

```bash
cd apps/web && npm run typecheck && npm test -- components/market/MarketProfilePanel.test.tsx
# tsc --noEmit passed; 1 Vitest test passed

rtk pytest tests/api tests/instrument_registry tests/adapter_registry tests/web -q
# Pytest: 64 passed
```
