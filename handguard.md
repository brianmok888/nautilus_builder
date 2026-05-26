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

## Segment 3 completion guard — job/runtime audit fields

Segment 3 is complete. Preserve these rules going forward:

- `BacktestJob` must keep `job_id`, `status`, `stage`, `created_by`, `created_at`, `updated_at`, `strategy_spec_version_id`, `adapter_profile_id`, `instrument_id`, `data_range`, `worker_id`, `result_artifact_refs`, and `event_stream_id`.
- API create/read/cancel responses must expose the backend-owned audit fields; frontend disconnects must not erase or cancel backend state.
- `RuntimeEvent` must keep `event_id`, `job_id`, `actor_type`, `actor_id`, `stage`, `level`, `message`, `timestamp`, and `metadata`; `progress_pct` remains a compatibility field and is mirrored into metadata.
- Worker success must use `SUCCEEDED`; do not reintroduce `COMPLETED` without updating source docs and tests.
- Redis runtime event payloads must preserve nested metadata during append/replay.

Segment 3 evidence:

```bash
rtk pytest tests/backtest_jobs tests/runtime_events tests/backtest_runner tests/api/test_backtest_job_routes.py tests/api/test_route_mounts.py tests/web/test_job_terminal_replay.py -q
# Pytest: 36 passed

python3 -m compileall -q packages/backtest_jobs packages/runtime_events services/workers services/api/routes/backtest_jobs.py
# compileall passed
```

## Segment 4 completion guard — NautilusTrader pin and fixture boundary

Segment 4 is complete. Preserve these rules going forward:

- `pyproject.toml` must keep `nautilus_trader==1.223.0` unless Daedalus runtime pin changes and Builder is updated in lockstep.
- Backtest configs and result artifacts must carry `nautilus_trader_version` and `engine_mode`.
- Fixture evidence must remain labeled `fixture`; injected engine evidence must remain labeled `injected_engine` until a concrete NautilusTrader engine adapter exists.
- Backtest configs must continue to reject credentials and expose `live_trading_enabled=False` and `execution_authority=False`.
- Do not claim real NautilusTrader backtest readiness from fixture results alone.

Segment 4 evidence:

```bash
rtk pytest tests/backtest_runner -q
# Pytest: 10 passed

python3 -m compileall -q packages/backtest_runner tests/backtest_runner
# compileall passed
```

## Master reconciliation guard — closed findings baseline

The 2026-05-24 findings closure baseline is verified. Preserve these stop conditions:

- Do not accept AI drafts without `validate_strategy_spec()` success.
- Do not remove hardguard forbidden credential/order terms from recursive validation.
- Do not let market-profile UI drift from backend fields: `adapter_id`, `instrument_id`, `data_type`, `timeframe`, `market_type`, `date_range`.
- Do not remove job/event audit fields or regress worker success from `SUCCEEDED` to `COMPLETED`.
- Do not change the Builder NautilusTrader pin without checking Daedalus runtime in lockstep.
- Do not treat fixture backtests as real NautilusTrader engine proof.
- Do not claim frontend readiness without Playwright passing against the local API + Next shell.

Master evidence:

```bash
python3 -m compileall -q packages services tests
rtk pytest tests/strategy_spec tests/strategy_validation tests/adapter_registry tests/instrument_registry tests/strategy_compiler tests/backtest_jobs tests/runtime_events tests/backtest_runner tests/lifecycle tests/strategy_registry tests/promotions tests/web tests/ai_builder tests/integration tests/workflow_spine tests/auth tests/api -q
# Pytest: 197 passed

cd apps/web && npm run typecheck && npm test && npm run build
# typecheck, Vitest, and build passed

cd apps/web && npm run test:e2e
# Playwright: 4 passed
```

## Deep review refresh guard — 2026-05-24 NT/Daedalus alignment

Preserve the closed top-findings baseline, but add these guards before stronger readiness claims:

1. **Pinned runtime guard**
   - Builder and Daedalus currently record `nautilus_trader==1.223.0`; do not change one without checking the other.
   - Before claiming NautilusTrader runtime/backtest readiness, run an import-time check that `importlib.metadata.version("nautilus_trader")` equals `packages.backtest_runner.engine_contract.NAUTILUS_TRADER_VERSION`.
   - A passing fixture/injected test does not prove the installed NautilusTrader engine version.

2. **Concrete backtest smoke guard**
   - Fixture mode remains `fixture`; injected protocol mode remains `injected_engine`.
   - Do not call either one a real NautilusTrader `BacktestEngine` run.
   - Add a minimal real NautilusTrader backtest smoke before promoting the engine boundary from WATCH to CLEAR.

3. **Promotion evidence guard**
   - Treat `/api/promotions/request` as the safe user-facing route.
   - Treat `/api/promotions/shadow` as internal/test-only unless it requires stored validation/backtest/no-lookahead/gate evidence IDs.
   - Never set `gate_compatibility=True` or evidence refs by fiat for readiness claims.

4. **Schema/docs drift guard**
   - If `doc/nautilus_builder_hardguards.md` lists v1 allowed blocks, either the executable `StrategySpec` schema must accept them or the docs/UI must clearly label the narrower MVP subset.
   - Current executable subset remains EMA/RSI plus `crossed_above`, `crossed_below`, `gt`, and `lt` until changed with tests.

5. **Warning hygiene guard**
   - Startup verification should not emit avoidable Pydantic model warnings.
   - Rename or alias warning-prone fields such as `BuilderPostgresConfig.schema` before treating E2E startup logs as clean.

## Production blocker closure guard — 2026-05-24

The current blocker-closure baseline is verified. Preserve these rules:

1. **Runtime version guard**
   - Keep Builder and Daedalus `nautilus_trader` pins in lockstep unless both repos are intentionally migrated.
   - Run `check_nautilus_runtime_version()` before claiming NautilusTrader runtime readiness.
   - A local/CI environment that imports a different `nautilus_trader` version fails the readiness contract.

2. **Real engine smoke guard**
   - Keep `fixture`, `injected_engine`, and `real_nautilus_engine_smoke` as distinct evidence modes.
   - Do not call the empty lifecycle smoke a full strategy/data replay.
   - Do not add credentials, venue adapters, live order submission, or Daedalus execution-lane imports to the smoke path.

3. **Promotion evidence guard**
   - `/api/promotions/shadow` must require explicit refs for: validation report, backtest result, no-lookahead report, gate-compatibility report, runtime-boundary report, and risk review.
   - Both `services/api/app.py` and `services/api/fastapi_app.py` must route shadow promotion through the same hardened helper.
   - Never fabricate `gate_compatibility=True`, coerce/accept empty evidence refs, accept missing strategy/compile identity, or accept string truthiness in a route wrapper.

4. **StrategySpec schema/docs guard**
   - `packages/strategy_spec/models.py`, `strategy_spec.schema.json`, frontend allowed blocks, and `doc/nautilus_builder_hardguards.md` must stay aligned.
   - Current executable indicators: `EMA`, `SMA`, `RSI`, `MACD`, `ATR`, `BollingerBands`, `VWAP`.
   - Current executable comparison operators: `crossed_above`, `crossed_below`, `gt`, `lt`, `gte`, `lte`, `eq`.
   - Current executable combinators: `all`, `any`; direct `not` remains out of scope unless implemented with tests.

5. **Hygiene guard**
   - Do not reintroduce `BuilderPostgresConfig.schema` as a model field; use `db_schema` and preserve the legacy `schema` input alias if needed.
   - README limitations must distinguish current implemented scaffolds from remaining production-integration gaps.

Closure evidence:

```bash
python3 -m compileall -q packages services tests
rtk pytest tests/strategy_spec tests/strategy_validation tests/adapter_registry tests/instrument_registry tests/strategy_compiler tests/backtest_jobs tests/runtime_events tests/backtest_runner tests/lifecycle tests/strategy_registry tests/promotions tests/web tests/ai_builder tests/integration tests/workflow_spine tests/auth tests/api -q
# Pytest: 215 passed

cd apps/web && npm run typecheck && npm test && npm run build && npm run test:e2e
# typecheck passed; Vitest 12 passed; Next build passed; Playwright 4 passed
```

## Catalog-backed replay closure start — 2026-05-24

Planning artifacts added for the remaining NautilusTrader readiness blocker: `docs/superpowers/specs/2026-05-24-catalog-backed-nautilus-replay-design.md` and `docs/superpowers/plans/2026-05-24-catalog-backed-nautilus-replay-implementation-plan.md`. The chosen design is a deterministic ParquetDataCatalog + BacktestNode replay using an official no-order SubscribeStrategy, preserving Builder's no-live-order boundary.

## Catalog-backed replay Segment 1 guard

Segment 1 is complete. Preserve these rules going forward:

- Keep `catalog_backed_replay_smoke` distinct from `fixture`, `injected_engine`, and empty `real_nautilus_engine_smoke` evidence modes.
- Catalog-backed replay evidence must include catalog path, data class, data count, strategy path, iterations, backtest start/end, metrics sections, and zero live authority booleans.
- The smoke may use deterministic packaged Nautilus test-kit market data helpers, but must not download data, connect to venues, import Daedalus, submit orders, create `TradeAction`, or accept credentials.
- Do not claim full production trading readiness from this smoke alone; full readiness still requires production dataset/artifact storage, StrategySpec-to-Nautilus strategy execution, and deployment evidence.

Segment 1 evidence:

```bash
rtk pytest tests/backtest_runner -q
# Pytest: 15 passed
```

## Catalog-backed replay Segment 2 guard

Segment 2 is complete. Preserve these wording boundaries:

- README and findings may say Builder has a catalog-backed Nautilus replay smoke over synthetic historical quote ticks.
- README and findings must not say this is production-scale StrategySpec-generated replay or full trading-production readiness.
- Keep the remaining production-worker gap visible until a real catalog-backed worker stores durable artifacts for user-selected datasets and compiled StrategySpec-generated strategies.

Segment 2 evidence:

```bash
rtk pytest tests/backtest_runner tests/integration/test_readme_readiness_hygiene.py -q
# Pytest: 17 passed
```

## Master reconciliation — catalog-backed Nautilus replay

The catalog-backed replay closure baseline is verified. Preserve these stop conditions:

- `CATALOG_BACKED_REPLAY_SMOKE_MODE` / `catalog_backed_replay_smoke` must remain distinct from fixture, injected-engine, and empty lifecycle modes.
- The catalog-backed smoke must keep using synthetic historical quote ticks or another deterministic local dataset; do not introduce network downloads into the smoke path.
- The smoke must keep `orders=0`, `positions=0`, `credentials_used=False`, `execution_authority=False`, and `live_trading_enabled=False`.
- Treat this as Nautilus data/strategy replay smoke evidence, not full trading-production readiness.
- Do not remove the remaining worker maturity warning until Builder has durable artifact storage, user-selected catalog inputs, StrategySpec-generated strategy execution, authz/tenant controls, and CI/deployment evidence.

Segment 3 focused evidence:

```bash
rtk pytest tests/backtest_runner tests/integration/test_readme_readiness_hygiene.py tests/integration/test_catalog_replay_ledger_updates.py -q
# Pytest: 18 passed
```

## Final verification — catalog-backed Nautilus replay closure

**Completed:** 2026-05-24.

Master evidence:

```bash
python3 -m compileall -q packages services tests
rtk pytest tests/strategy_spec tests/strategy_validation tests/adapter_registry tests/instrument_registry tests/strategy_compiler tests/backtest_jobs tests/runtime_events tests/backtest_runner tests/lifecycle tests/strategy_registry tests/promotions tests/web tests/ai_builder tests/integration tests/workflow_spine tests/auth tests/api -q
# Pytest: 218 passed

cd apps/web && npm run typecheck && npm test && npm run build && npm run test:e2e
# typecheck passed; Vitest: 8 files / 12 tests passed; Next build passed; Playwright: 4 passed
```

Authority grep for live-order/credential/Daedalus execution terms found only guard tables, negative tests, false authority booleans, and credential-rejection paths. No Builder live-order path was introduced.

## Production runtime readiness Segment 1 guard — durable artifacts

Segment 1 is complete. Preserve these rules:

- Backtest/result/promotion evidence intended for production claims must be persisted as scoped artifacts, not only returned as in-memory dictionaries.
- Builder artifact refs must remain user/project scoped (`artifact://builder/{project_id}/{user_id}/...`).
- Cross-project or cross-user artifact reads must raise `ProjectScopeError`.
- Artifact payloads must keep checksum evidence; do not silently ignore checksum mismatches.
- The local JSON store is a durable adapter seam, not proof of production object-storage deployment.

Evidence:

```bash
rtk pytest tests/artifact_store/test_local_json_artifact_store.py -q
# Pytest: 3 passed
```

## Production runtime readiness Segment 2 guard — catalog dataset selection

Segment 2 is complete. Preserve these rules:

- Backtest jobs that claim catalog-backed readiness must carry a concrete `dataset_id` and `catalog_path`.
- Dataset selection must validate `adapter_id`, `instrument_id`, `data_type`, `timeframe`, `market_type`, and `date_range`; do not infer a dataset from instrument alone.
- Catalog datasets are user/project-scoped artifacts; cross-project selection must raise `ProjectScopeError`.
- Do not download external market data implicitly in tests or smoke paths.
- Do not treat `dataset_id="unspecified"` legacy compatibility as production dataset evidence.

Evidence:

```bash
rtk pytest tests/catalog_datasets tests/backtest_jobs -q
# Pytest: 8 passed
```

## Production runtime readiness Segment 3 guard — StrategySpec replay

Segment 3 is complete. Preserve these rules:

- `strategy_spec_catalog_replay` must stay distinct from fixture, injected-engine, empty lifecycle smoke, and generic subscribe smoke modes.
- StrategySpec replay must use `packages.nautilus_rule_graph.strategy:RuleGraphBacktestStrategy` and carry the validated StrategySpec plus compile hash in strategy config.
- The rule-graph replay strategy must remain no-order: subscribe/observe only, zero orders, zero positions, no credentials, `execution_authority=False`, and `live_trading_enabled=False`.
- Dataset/spec mismatches must fail before the replay is used as evidence.
- Worker replay evidence must be persisted through scoped artifact storage before it is used for readiness or promotion claims.

Evidence:

```bash
rtk pytest tests/backtest_runner -q
# Pytest: 17 passed
```

## Production runtime readiness Segment 4 guard — tenant authz

Segment 4 is complete. Preserve these rules:

- Backtest jobs must keep `user_id`, `project_id`, `dataset_id`, and `catalog_path` in audit payloads.
- Package-level job access with a supplied `UserProjectContext` must enforce `assert_same_project()`.
- API scoped read/cancel requests must return `403` for cross-project or cross-user access.
- Do not treat unscoped legacy access as production auth; production deployment must route real tokens/context into these package checks.
- Do not move tenant-policy enforcement exclusively into route code; package services must remain enforceable directly.

Evidence:

```bash
rtk pytest tests/auth tests/backtest_jobs tests/api/test_backtest_job_routes.py -q
# Pytest: 21 passed
```

## Production runtime readiness Segment 5 guard — CI/deployment evidence

Segment 5 is complete. Preserve these rules:

- CI evidence must include Python compile checks, Nautilus runtime pin verification, artifact/dataset tests, backtest runner tests, and frontend type/unit/build/e2e checks.
- Deployment evidence must keep the no-live-order boundary explicit.
- Do not claim cloud/object-storage production readiness from the local JSON store alone.
- Do not claim production auth readiness until real auth middleware/token propagation feeds `UserProjectContext` into package checks.
- Keep CI templates and README limitations aligned with the actual verification commands.

Evidence:

```bash
rtk pytest tests/integration/test_operability_baseline.py tests/integration/test_readme_readiness_hygiene.py -q
# Pytest: 8 passed
```

## Master reconciliation guard — production runtime readiness closure

Preserve this baseline:

- Durable evidence must be artifact-backed with checksum and scope metadata.
- Dataset-backed replay must require explicit user-selected dataset identity and full profile match.
- StrategySpec replay must remain no-order and must keep `orders=0`, `positions=0`, `credentials_used=False`, `execution_authority=False`, and `live_trading_enabled=False`.
- Worker transitions with a supplied context must enforce job scope before mutating job state.
- API `403 forbidden` behavior for cross-project job access must remain covered by tests.
- CI/deployment docs must not claim cloud object storage, real auth middleware, production dataset ingestion, or live trading authority until those are actually implemented and verified.

Master evidence:

```bash
rtk pytest tests/backtest_runner/test_worker_integration.py::test_worker_rejects_context_outside_job_scope -q
# RED: worker did not reject cross-project context
# GREEN: Pytest: 1 passed

rtk pytest tests/strategy_spec tests/strategy_validation tests/adapter_registry tests/instrument_registry tests/strategy_compiler tests/backtest_jobs tests/runtime_events tests/backtest_runner tests/lifecycle tests/strategy_registry tests/promotions tests/web tests/ai_builder tests/integration tests/workflow_spine tests/auth tests/api tests/artifact_store tests/catalog_datasets -q
# Pytest: 234 passed
```

## Deep review handguard — 2026-05-25 inventory-first semantic legacy/deprecation closure

Preserve these hardguards before claiming stronger readiness than the current local contract baseline.

### Catalog and Nautilus replay guards

- Synthetic catalog smokes must be labeled as synthetic/test-kit evidence. They must not be described as proof that user-selected catalog data was replayed.
- A production/user-dataset replay mode must read from an existing selected catalog and fail closed when the catalog is missing, empty, out of scope, or mismatched. It must not write `TestDataStubs` rows into the selected dataset path.
- Every replay evidence payload must declare `dataset_source` (`synthetic_test_kit`, `user_catalog`, or another explicit value), data class, row count, dataset ID, catalog path, spec version, compile hash, and no-order booleans.
- `ParquetDataCatalog` paths used by workers must be under a configured safe root or a trusted registry-managed path. Do not accept arbitrary absolute paths from API payloads as write targets.
- Keep `orders=0`, `positions=0`, `credentials_used=False`, `execution_authority=False`, and `live_trading_enabled=False` for Builder-owned replays.

### Auth, tenant, and artifact guards

- Production API routes must derive `UserProjectContext` from verified auth middleware/token dependencies, not from user-supplied query/body values.
- Client-supplied `user_id`/`project_id` may exist only as test/dev compatibility and must not be used as production authorization evidence.
- Scoped access checks must remain in package services, not only in route wrappers.
- Promotion evidence refs used for readiness must resolve to scoped Builder artifact refs (`artifact://builder/{project_id}/{user_id}/...`) and pass checksum/scope/type verification.
- Legacy unscoped refs such as `artifact://backtests/...` or `artifact://validation/...` are fixture/compatibility examples only.

### Registry and StrategySpec semantic guards

- Market catalog, catalog dataset selection, and StrategySpec replay must agree on supported data types. If replay requires `quote_ticks`, the instrument registry and UI contracts must expose `quote_ticks`; otherwise replay must consume the registry-approved data type.
- Do not create backtest jobs until adapter, instrument, data type, timeframe, market type, date range, dataset ID, and catalog path have been validated against the registry/dataset contracts.
- Do not use `backtest_order_intent` or any other order-intent wording for Builder no-order artifacts. Reserve order-intent / `TradeAction` language for Daedalus gate/execution contracts.
- `dataset_id="unspecified"` is legacy compatibility only and must never be accepted as production dataset evidence.

### AI/advisory and Telegram guards

- Builder must not import or directly call LangChain, LangGraph, EvoMap/evolver, or Daedalus advisory/runtime packages from execution paths unless a new reviewed advisory-only seam is added.
- Advisory outputs may inform drafts, evidence summaries, or shadow analysis only; they must not create, gate, submit, cancel, or modify orders.
- Builder currently has no aiogram-dialog surface. If one is added later, it must be downstream/observational only, call `setup_dialogs()` exactly once in its own UI bootstrap, use stable dialog/widget IDs, and must not affect Nautilus/Daedalus runtime state.

### Required verification before closing the 2026-05-25 findings

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

Additional closure tests required for the new findings:

- user-catalog replay fails if the catalog has no pre-existing matching data;
- user-catalog replay does not write synthetic rows;
- catalog paths outside the configured safe root are rejected;
- FastAPI routes reject missing/invalid bearer auth and ignore spoofed body/query scope;
- promotion refs are resolved through scoped artifact storage and checksum-verified;
- market catalog and StrategySpec replay supported data types are asserted by one shared contract test;
- `backtest_order_intent` is removed or quarantined behind an explicit legacy test.

## Findings closure Segment 1 guard — catalog trust and read-only user replay

Segment 1 is complete. Preserve these rules:

- `strategy_spec_catalog_replay` is the production/user-catalog mode and must be read-only against the selected catalog.
- `strategy_spec_synthetic_catalog_smoke` is the only StrategySpec replay path allowed to write Nautilus test-kit quote ticks, and its evidence must declare `dataset_source=synthetic_test_kit`.
- User-catalog replay must declare `dataset_source=user_catalog`, require `catalog_root`, validate with `CatalogPathPolicy`, and fail closed if the catalog is missing, empty, out of scope, or symlink-traversed.
- User-catalog replay evidence must include catalog data count, manifest checksum, and manifest file count before it is used for readiness claims.
- Worker StrategySpec replay must pass a configured catalog root; do not reintroduce arbitrary worker writes under API-supplied catalog paths.

Evidence:

```bash
rtk pytest tests/catalog_datasets tests/backtest_runner -q
# Pytest: 26 passed
```

## Findings closure Segment 2 guard — auth-derived scope and job validation

Segment 2 is complete. Preserve these rules:

- FastAPI backtest job create/read/cancel routes must derive `UserProjectContext` from verified bearer auth, not from `user_id`/`project_id` supplied by clients.
- Strict API mode must ignore spoofed body/query scope and must return 401 for missing/invalid bearer auth.
- Strict backtest job creation must validate adapter, instrument, data type, timeframe, market type, date range, dataset ID, and catalog path through registry-owned contracts before creating a job.
- Route-level validation must return typed 4xx responses for missing/mismatched fields; do not reintroduce raw `KeyError` server errors for malformed payloads.
- Package-level job scope checks must remain in `BacktestJobService` for direct worker/service access.

Evidence:

```bash
rtk pytest tests/auth tests/api tests/backtest_jobs tests/catalog_datasets -q
# Pytest: 59 passed
```

## Findings closure Segment 3 guard — scoped promotion evidence

Segment 3 is complete. Preserve these rules:

- Promotion readiness evidence intended for strict/runtime claims must use scoped Builder artifact refs, not legacy unscoped fixture refs.
- Strict promotion evidence must resolve through the artifact store with the auth-derived `UserProjectContext`.
- Strict promotion evidence must fail on wrong scope, checksum mismatch, missing artifact, or artifact type mismatch.
- `PromotionRequest.evidence_checksums` must be retained for audit whenever strict evidence is resolved.
- Legacy refs such as `artifact://backtests/...` are fixture/dev compatibility only and must require explicit non-strict mode.

Evidence:

```bash
rtk pytest tests/promotions tests/artifact_store tests/api -q
# Pytest: 65 passed
```

## Findings closure Segment 4 guard — quote-tick replay and no-order naming

Segment 4 is complete. Preserve these rules:

- If StrategySpec replay requires `quote_ticks`, the market catalog and API validation must expose and accept `quote_ticks` for the same instrument/profile.
- Adapter-supported data modes are not enough; `InstrumentRegistryService` must also validate instrument-level supported data types.
- Builder no-order backtest artifacts must use `backtest_signal_observation` / `BacktestSignalObservation` wording.
- Do not reintroduce `backtest_order_intent` or `BacktestOrderIntent` into Builder no-order source truth.
- Reserve order-intent / `TradeAction` terminology for Daedalus-owned gate/execution contracts.

Evidence:

```bash
rtk pytest tests/instrument_registry tests/strategy_compiler tests/api tests/backtest_runner tests/integration/test_semantic_legacy_closure.py -q
# Pytest: 67 passed
```

## Master reconciliation guard — 2026-05-25 findings closure

Preserve this closure baseline:

- User-catalog StrategySpec replay is read-only, root-validated, and manifest-recorded. Synthetic StrategySpec evidence must stay in `strategy_spec_synthetic_catalog_smoke` and must declare `dataset_source=synthetic_test_kit`.
- Strict FastAPI backtest job routes derive scope from bearer auth and validate market profile plus scoped catalog dataset before job creation.
- Strict FastAPI shadow-promotion routes derive scope from bearer auth and resolve scoped artifact evidence when an artifact store is configured.
- Strict promotion evidence must verify Builder ref shape, user/project scope, checksum, and artifact type; successful strict requests must carry `evidence_checksums`.
- Market catalog and StrategySpec replay must stay aligned on `quote_ticks` for the replay-supported Builder instrument profile.
- Builder no-order artifacts must keep `backtest_signal_observation` / `BacktestSignalObservation` wording and must not reintroduce order-intent terminology.
- Non-strict legacy API/service paths are fixture/dev compatibility only and must not be cited as production readiness evidence.

Master evidence:

```bash
python3 -m compileall -q packages services tests
rtk pytest tests -q
# Pytest: 256 passed

python3 - <<'PY'
from packages.backtest_runner.runtime_check import check_nautilus_runtime_version
status = check_nautilus_runtime_version()
assert status.is_match, status.message
PY
# nautilus_trader runtime matches pinned version 1.223.0

cd apps/web && npm run typecheck && npm test -- --run && npm run build && npm run test:e2e
# typecheck passed; Vitest: 12 passed; Next build passed; Playwright: 4 passed

git diff --check
# passed
```

## Deep review handguard — 2026-05-25 post-closure inventory review

This review found new blockers after the prior findings closure. Preserve the prior closed baseline, but do not make production-readiness, strict promotion-readiness, or tenant-safe API claims until the following guards are executable.

### Promotion evidence binding guards

- Strict promotion evidence must be both artifact-backed and semantically bound to the request.
- Every strict evidence artifact must resolve under the auth-derived `UserProjectContext` and must match the requested `compile_hash` plus strategy/version/result/job lineage metadata appropriate to the evidence type.
- Missing, corrupt, wrong-scope, wrong-type, checksum-mismatched, or stale/wrong-compile evidence must fail as typed 4xx/API domain errors, never as uncaught `FileNotFoundError`, `KeyError`, or raw JSON errors.
- `PromotionRequest.evidence_checksums` is necessary but not sufficient; checksums prove payload integrity, not relevance to the promotion request.

Required closure tests:

```bash
rtk pytest tests/promotions tests/artifact_store tests/api -q
# Must include negative cases for missing scoped artifact and wrong compile_hash/strategy evidence.
```

### Catalog traversal and root-policy guards

- Catalog path allowlisting must cover both the selected catalog directory and every file read for manifest/evidence generation.
- Manifest traversal must reject or skip symlinked files and symlinked directories; every resolved file candidate must remain under the resolved catalog path/root before hashing.
- Strict catalog dataset registries must be visibly root-policy configured. Do not accept absolute or relative catalog paths in strict API/worker paths unless a configured catalog root normalizes and allowlists them.
- User-catalog replay remains read-only. Synthetic smoke may write only to the controlled synthetic smoke catalog and must keep `dataset_source=synthetic_test_kit`.

Required closure tests:

```bash
rtk pytest tests/catalog_datasets tests/backtest_runner/test_strategy_spec_catalog_replay.py -q
# Must include nested symlink-in-catalog manifest regression and strict registry-without-root rejection.
```

### Tenant/auth scope guards

- FastAPI auth-derived scope must be consistent across all production-facing routes, not only backtest jobs and strict shadow promotion.
- Strategy draft/version routes, workflow result routes, suggestion routes, lineage routes, runtime-event replay, AI apply/draft audit access, and promotion-request routes must either derive `UserProjectContext` from bearer auth or be explicitly documented/tested as fixture/dev-only.
- Repository methods that store `project_id` must support scoped reads; do not expose `result_id`, `strategy_lineage_id`, or `ai_thread_id` lookups without project/user checks.
- The lightweight `ApiApp` can stay dependency-free for contract tests, but it must not be cited as production authorization evidence.

Required closure tests:

```bash
rtk pytest tests/auth tests/api tests/workflow_spine tests/strategy_spec tests/ai_builder -q
# Must include cross-project denial for strategies, workflow results/suggestions/lineage, runtime events, and AI apply/audit records.
```

### Storage identifier guards

- Builder-owned SQL schema/table and Redis namespace identifiers must be constrained to safe identifier shapes.
- Do not interpolate unvalidated schema or namespace values into SQL identifiers or stream keys.
- If a real Postgres driver replaces the SQLite seam, use driver-supported identifier quoting/composition instead of string concatenation.

Required closure tests:

```bash
rtk pytest tests/workflow_spine tests/runtime_events -q
# Must reject unsafe schema/namespace strings and preserve valid builder-owned defaults.
```

### AI/advisory provenance guards

- AI Builder output remains advisory-only and must pass StrategySpec validation before apply.
- Applying an AI draft must require non-empty `ai_thread_id`, `improvement_cycle_id`, `strategy_lineage_id`, and `strategy_version_id`.
- API-level AI audit must be durable or explicitly fixture/dev-only; do not claim LangChain/LangGraph/EvoMap-style persistence/human-in-the-loop traceability from an ephemeral per-request in-memory store.
- No LangChain/LangGraph/EvoMap runtime dependency should be added unless the integration is explicitly approved and remains advisory, degraded-mode safe, and unable to affect live execution directly.

Required closure tests:

```bash
rtk pytest tests/ai_builder tests/workflow_spine tests/integration -q
# Must include blank-provenance rejection and durable audit evidence for API apply paths.
```

### Required master verification before closing this review

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

Do not close the 2026-05-25 post-closure blockers until the markdown ledgers, source tests, and implementation all agree on the same stricter guarantees.

## R2 Segment 1 completion guard — promotion lineage-bound evidence

Segment 1 is complete. Preserve these rules going forward:

- Strict promotion evidence must match the requested `compile_hash` and `strategy_version` / `strategy_version_id` in artifact payload or metadata.
- Artifact ref shape/scope/type/checksum verification is necessary but not sufficient; relevance to the promotion request is required before `PromotionRequest` is returned.
- Missing/corrupt scoped artifact evidence must fail as a typed 4xx/domain error, never as uncaught `FileNotFoundError`, raw JSON decode, or `KeyError`.
- Test helpers that create strict promotion artifacts must include lineage metadata.

Segment 1 evidence:

```bash
rtk pytest tests/promotions tests/artifact_store tests/api/test_fastapi_app.py -q
# Pytest: 37 passed
```

## R2 Segment 2 completion guard — catalog traversal/root policy

Segment 2 is complete. Preserve these rules going forward:

- Catalog manifest generation must reject symlinked files and directories and must not read resolved paths outside the selected catalog tree.
- Strict catalog dataset registration/selection must require a configured `catalog_root`; no-root registries are fixture/dev compatibility only.
- Strict backtest job creation must pass `strict_root_policy=True` when selecting a catalog dataset.
- User-catalog replay remains read-only; synthetic smoke remains the only path allowed to write deterministic test-kit data.

Segment 2 evidence:

```bash
rtk pytest tests/catalog_datasets tests/backtest_runner tests/api/test_backtest_job_routes.py tests/api/test_fastapi_app.py -q
# Pytest: 46 passed
```

## R2 Segment 3 completion guard — FastAPI tenant/project scoping

Segment 3 is complete. Preserve these rules going forward:

- FastAPI production-facing routes must derive `UserProjectContext` from bearer auth rather than trusting request body/query scope.
- Strategy records created through FastAPI strict routes must carry user/project ownership; list/detail/update/version reads must enforce that ownership.
- Workflow results, suggestions, and lineage projection reads must check project scope before returning metrics, artifacts, or AI messages.
- Runtime event replay, AI draft/apply surfaces, and promotion-request surfaces must stay auth-gated in FastAPI; lightweight `ApiApp` remains fixture/dev-only for dependency-free contract tests.

Segment 3 evidence:

```bash
rtk pytest tests/api tests/workflow_spine tests/strategy_spec tests/runtime_events -q
# Pytest: 98 passed
```

## R2 Segment 4 completion guard — storage identifiers and AI provenance

Segment 4 is complete. Preserve these rules going forward:

- SQL schema/table identifiers and Redis namespaces must pass `safe_storage_identifier()` before interpolation or namespace construction.
- Redis namespace separators belong in stream suffixes, not in the Builder namespace value itself.
- Applying an AI draft must require non-empty `ai_thread_id`, `improvement_cycle_id`, `strategy_lineage_id`, and `strategy_version_id`.
- FastAPI AI apply must use a reused/injected audit store or service; do not recreate an ephemeral audit store for each request.
- AI remains advisory-only and validation-gated; no LangChain/LangGraph/EvoMap runtime dependency was added.

Segment 4 evidence:

```bash
rtk pytest tests/workflow_spine tests/runtime_events tests/ai_builder tests/api -q
# Pytest: 101 passed
```

## R2 Segment 5 completion guard — fixture refs and frontend verification noise

Segment 5 is complete. Preserve these rules going forward:

- Fixture/dev evidence must be visibly labeled as fixture-only and must not be confused with scoped Builder production artifacts.
- Fixture backtest outputs should use `fixture://` refs and carry `fixture_evidence_only=true`.
- Strict FastAPI result routes must require repository-owned scoped results; compatibility dashboard fallback remains `ApiApp`/fixture-dev only.
- Keep Vitest on the ESM `.mts` config path and avoid reintroducing Vite CJS Node API warnings.
- Keep the Playwright web server command from exporting conflicting `FORCE_COLOR`/`NO_COLOR` settings.

Segment 5 evidence:

```bash
rtk pytest tests/backtest_runner tests/api tests/web tests/integration -q
# Pytest: 121 passed

cd apps/web && npm test -- --run
# Vitest: 12 passed; no Vite CJS warning observed
```

## Master guard — 2026-05-25 R2 closure baseline

The R2 findings closure baseline is verified. Preserve these stop conditions:

- Do not accept strict promotion evidence unless artifacts are scoped, checksummed, type-correct, and bound to the requested compile hash plus strategy lineage.
- Do not hash catalog manifest entries that are symlinks or resolve outside the selected catalog tree.
- Do not expose production FastAPI strategy/workflow/runtime/AI/promotion routes without bearer-derived `UserProjectContext`.
- Do not interpolate SQL schema/table or Redis namespace identifiers unless they pass the safe storage identifier policy.
- Do not apply AI drafts without non-empty thread/cycle/lineage/version provenance and durable/reused audit storage.
- Do not expose fixture evidence as production evidence; keep fixture refs visibly `fixture://` and fixture-dev-only.
- Keep frontend verification warning cleanup in place: ESM Vitest config and no conflicting Playwright color env.

Master evidence:

```bash
python3 -m compileall -q packages services tests
rtk pytest tests -q
# Pytest: 278 passed

python3 - <<'PY'
from packages.backtest_runner.runtime_check import check_nautilus_runtime_version
status = check_nautilus_runtime_version()
assert status.is_match, status.message
PY
# nautilus_trader runtime matches pinned version 1.223.0

cd apps/web && npm run typecheck && npm test -- --run && npm run build && npm run test:e2e
# typecheck passed; Vitest 12 passed; Next build passed; Playwright 4 passed

git diff --check
# passed
```

## Post-implementation code-review guard — 2026-05-25

The R2 closure diff was reviewed after implementation. Keep the final gating rule:

- Do not weaken any strict guard added in Segments 1-5 without adding a failing regression first and preserving a stricter replacement.

Review verdict: **APPROVE / CLEAR** for local repo-contract closure. Deployment watch items remain external to this diff.

## 11. Frontend API/proxy error guard

When adding frontend API calls:

- Route all calls through `apps/web/lib/api.ts`.
- Do not call `response.json()` directly on unknown responses.
- Preserve clear diagnostics for VM staging: status, URL, content type, body snippet, and `BUILDER_API_BASE_URL` / `NEXT_PUBLIC_API_BASE_URL` guidance.
- Treat HTML/text/empty API responses as API/proxy configuration failures, not as generic JSON parser errors.

Minimum regression command:

```bash
cd apps/web && npm test -- --run lib/api.test.ts
```

## 12. Frontend visual shell guard

When improving the Builder frontend:

- Keep `apps/web/app/globals.css` as the dependency-free visual shell unless a future task explicitly approves a UI framework.
- Preserve `apps/web/app/layout.tsx` importing `./globals.css`.
- Do not add Tailwind, MUI, Chakra, or another UI library for basic shell polish without an explicit dependency decision.
- Keep UI copy and affordances authoring/observational/advisory only; visual polish must not imply live execution authority.
- Keep class tokens such as `.app-shell`, `.dashboard-grid`, `.card`, `.panel`, `.form-grid`, `.status-badge`, and `.terminal-card` covered by tests.

Minimum regression command:

```bash
rtk pytest tests/web/test_app_shell_contract.py tests/web/test_frontend_infrastructure.py -q
```

## 13. VM staging guard

For remote VM staging:

- Start the API on a host/port reachable by the Next server and browser.
- Set `BUILDER_API_BASE_URL` for Next server-side API calls when the API is not on `127.0.0.1:8000` from the web process.
- Set `NEXT_PUBLIC_API_BASE_URL` only when the browser should call the API origin directly; otherwise rely on Next rewrites to `/api/:path*` and `/health/backend`.
- If the UI reports `expected JSON but received text/html`, inspect the URL in the `ApiError`; it usually means the frontend reached a proxy/HTML error page instead of the Builder API.
- Do not claim full frontend E2E readiness until Playwright runs with installed browsers on the target or equivalent provisioned environment.

## 14. Frontend UI/API post-review guard

The 2026-05-25 frontend UI/API hardening diff was reviewed as **APPROVE / CLEAR**. Preserve these review outcomes:

- JSON error payloads must stay parseable and must not be reported as empty responses.
- Non-JSON HTML/text failures must stay actionable for VM proxy/API-base debugging.
- Visual shell changes must remain dependency-free and must not imply live order authority.
- Treat Playwright/browser E2E as the remaining readiness watch item for frontend deployment claims.

## 15. Test dependency reproducibility guard

Clean VM/CI environments must be able to run the documented Python contract suite with repository-declared dependencies only.

- Keep test-only parser/tooling dependencies in `[project.optional-dependencies].test`, not as ad-hoc VM installs.
- Keep `uv.lock` synchronized after changing `pyproject.toml` dependency metadata.
- `tests/strategy_spec/test_schema_valid.py` validates a packaged YAML StrategySpec example, so the test extra must include PyYAML while that test remains YAML-backed.
- Do not move PyYAML into runtime dependencies unless production Builder code begins importing `yaml`.
- Prefer manifest/lock fixes over remote-VM one-off package installs.

Minimum regression commands:

```bash
uv sync --extra test
rtk pytest tests/integration/test_operability_baseline.py::test_python_project_declares_runtime_and_test_dependencies tests/strategy_spec/test_schema_valid.py::test_example_yaml_loads_as_valid_strategy_spec -q
```

## 16. OpenAI-compatible AI draft provider guard

The OpenAI-compatible draft provider is optional and advisory-only.

- Activate it only when `OPENAI_API_KEY`, `OPENAI_BASE_URL`, and `OPENAI_MODEL` are all set.
- Treat `OPENAI_BASE_URL` as an OpenAI-compatible API root; normalize it to a chat-completions endpoint without hardcoding a single vendor.
- Never store or echo `OPENAI_API_KEY` in audit records, errors, logs, docs, or tests.
- Store prompt text and response metadata needed for auditability, such as provider name, model, endpoint URL without credentials, response ID, finish reason, and usage.
- Model output must be parsed as a JSON object and passed through `validate_strategy_spec()` before any draft is accepted or applied.
- Reject malformed JSON, non-object content, missing StrategySpec fields, forbidden `submit_order` / `TradeAction` references, and credential references.
- Keep `validation.output_mode` as `signal_preview_only`; the provider must not add live trading authority, Daedalus coupling, automatic promotion, or order submission APIs.

Minimum regression command:

```bash
rtk pytest tests/ai_builder/test_openai_compatible_provider.py tests/ai_builder/test_ai_output_must_validate.py tests/ai_builder/test_persistent_audit_store.py -q
```

## Segment AI-2 completion guard — OpenAI-compatible draft provider

Segment AI-2 is complete. Preserve these rules going forward:

- FastAPI AI drafting may opt into an OpenAI-compatible provider only through complete `OPENAI_API_KEY`, `OPENAI_BASE_URL`, and `OPENAI_MODEL` env configuration.
- Missing OpenAI env must keep deterministic advisory drafting available for local/dev/test workflows.
- Do not introduce an OpenAI SDK dependency unless a future task explicitly accepts the dependency and adds tests for provider compatibility.
- Keep audit records free of API keys and authorization headers; response metadata is enough for lineage.
- Keep malformed provider responses as rejected drafts, not accepted specs and not uncaught API crashes.
- Keep credential-bearing prompts rejected before audit persistence.
- Keep `validate_strategy_spec()` as the final acceptance gate for every provider output.

Segment AI-2 evidence:

```bash
rtk pytest tests/ai_builder -q
# Pytest: 17 passed

python3 -m compileall -q packages services tests
rtk pytest tests/strategy_spec tests/strategy_validation tests/adapter_registry tests/instrument_registry tests/strategy_compiler tests/backtest_jobs tests/runtime_events tests/backtest_runner tests/lifecycle tests/strategy_registry tests/promotions tests/web tests/ai_builder tests/integration tests/workflow_spine tests/auth tests/api -q
# Pytest: 278 passed
```

## 17. VM web/API proxy and LLM config UI guard

For VM/staging web deployments:

- Use `BUILDER_API_BASE_URL` for server-side Next rewrites when the API is reachable from the web process.
- Keep `NEXT_PUBLIC_API_BASE_URL` optional for browser-direct API calls only; do not require browser direct cross-origin API access when the Next proxy is available.
- Keep `/api/:path*` and `/health/backend` rewrites pointed at the selected API base URL.
- Verify staged proxying with `curl -i http://<web-host>:3000/api/adapters` and `curl -i http://<web-host>:3000/api/strategies`; both should return JSON, not `500 Internal Server Error`.

For LLM configuration UI:

- `/config` is a UI draft/configuration workspace, not a secret store.
- Do not add browser-side API-key/password inputs for model providers.
- Display env labels such as `OPENAI_BASE_URL`, `OPENAI_MODEL`, and server-side-only `OPENAI_API_KEY` guidance without persisting secrets.
- Keep provider/model config advisory-only and bound to `validate_strategy_spec()`, `signal_preview_only`, no credentials, no `submit_order`, no `TradeAction`, and manual promotion.
- Do not add LangChain/LangGraph/EvoMap runtime dependencies from this UI surface without a new advisory-only design and tests.

Minimum regression commands:

```bash
rtk pytest tests/web/test_frontend_infrastructure.py tests/web/test_config_ui_contract.py -q
cd apps/web && npm test -- --run components/config/ModelConfigTabs.test.tsx && npm run test:e2e
```

Segment VM-API-1 / CONFIG-1 evidence:

```bash
python3 -m compileall -q packages services tests
rtk pytest tests/strategy_spec tests/strategy_validation tests/adapter_registry tests/instrument_registry tests/strategy_compiler tests/backtest_jobs tests/runtime_events tests/backtest_runner tests/lifecycle tests/strategy_registry tests/promotions tests/web tests/ai_builder tests/integration tests/workflow_spine tests/auth tests/api -q
# Pytest: 280 passed

cd apps/web && npm run typecheck && npm test && BUILDER_API_BASE_URL=http://192.168.4.82:8000 npm run build && npm run test:e2e
# typecheck passed; Vitest: 18 passed; build passed; Playwright: 4 passed
```

## 18. Ant Design operator UI guard

The 2026-05-26 UI polish segment explicitly approves Ant Design React for the Builder web app.

- `antd` and `@ant-design/icons` are approved frontend dependencies for the Next.js/React app.
- Do not migrate this repo to Vue or add `@ant-design-vue/pro-layout`; QuantDinger-Vue is UX inspiration only.
- Keep the AntD shell visibly advisory-only: sidebar/topbar should keep no-live-authority/manual-promotion/signal-preview cues visible.
- Do not add browser API-key/password inputs for LLM providers; secrets remain backend env/config only.
- Do not add `submit_order`, `TradeAction`, Daedalus execution coupling, automatic promotion, or live-trading controls to frontend components.
- Avoid deprecated AntD APIs that emit runtime/test warnings; current closed warnings included `Space direction`, `Alert message`, `List`, and `Steps.description`.
- Watch bundle size before adding charts; prefer lazy route-level loading for backtest/equity curves.
- `npm audit --omit=dev --audit-level=moderate` currently reports a moderate Next/PostCSS advisory with a breaking force-fix path; do not apply `npm audit fix --force` without a reviewed framework-upgrade plan.

Minimum regression commands:

```bash
rtk pytest tests/web/test_antd_operator_ui_contract.py tests/web/test_app_shell_contract.py tests/web/test_frontend_infrastructure.py tests/web/test_config_ui_contract.py -q
cd apps/web && npm run typecheck && npm test && npm run build && npm run test:e2e
```

Segment UI-ANTD-1 final evidence refresh:

```bash
git diff --check
rtk pytest tests/web/test_antd_operator_ui_contract.py tests/web/test_app_shell_contract.py tests/web/test_frontend_infrastructure.py tests/web/test_config_ui_contract.py -q
python3 -m compileall -q packages services tests
rtk pytest tests/strategy_spec tests/strategy_validation tests/adapter_registry tests/instrument_registry tests/strategy_compiler tests/backtest_jobs tests/runtime_events tests/backtest_runner tests/lifecycle tests/strategy_registry tests/promotions tests/web tests/ai_builder tests/integration tests/workflow_spine tests/auth tests/api -q
cd apps/web && npm run typecheck && npm test && npm run build && npm run test:e2e
cd apps/web && npm audit --omit=dev --audit-level=high
# diff check passed; Pytest focused 15 passed; Pytest targeted 284 passed; Vitest 18 passed; Playwright 4 passed; audit high exited 0 with only moderate Next/PostCSS advisory.
```

## 19. AI prompt UI and compact workflow guard

The AI prompt UI is allowed to turn operator text into advisory Builder StrategySpec drafts only.

- Keep `Apply to Builder` disabled unless the draft response has `accepted: true`.
- Show validation errors and rejected status for invalid drafts; do not silently repair or apply rejected output in the browser.
- Preserve `ai_thread_id`, `improvement_cycle_id`, `strategy_lineage_id`, and `strategy_version_id` in apply payloads.
- Do not add browser-side OpenAI/API-key/password inputs to this prompt UI.
- Do not let this UI create backtest jobs, submit live orders, create promotion approvals, or bypass `validate_strategy_spec()`.
- Keep the dashboard prompt-first and compact; avoid reintroducing equal-weight scaffold panels that obscure the natural user workflow.

Minimum regression commands:

```bash
pytest tests/web/test_ai_copilot_frontend.py -q
cd apps/web && npm test -- --run components/ai-builder/AiStrategyCopilot.test.tsx
```

Reference-project boundary note:

- QuantDinger / QuantDinger-Vue may be used as product-structure inspiration only.
- Do not copy source code, styling, branding, or licensed assets from the source-available frontend.
- Do not port Vue, Vuex, Ant Design Vue, QuickTradePanel, exchange account binding, live execution output, or portfolio trading controls into Nautilus Builder.
- Allowed carry-over: high-level information architecture, compact operator layout patterns, prompt → strategy → backtest → review workflow ordering, and clear separation between API, layout, page, and reusable component modules.

## PMBT-inspired Backtest Center guard — Segment BT-1

**Added:** 2026-05-26 10:05:52Z

Adopt architecture patterns only, not source code, from external backtesting repos. Builder backtest-center contracts must:

- bind every run to strategy lineage/version, compile hash, dataset provenance, engine mode, and timestamps;
- require artifact refs to include safe scope, checksum, and media type;
- reject artifact URI traversal and unscoped local file refs;
- treat fixture refs as dev evidence only;
- expose report summaries for UI/analysis without implying live authority;
- keep `live_trading_enabled=false`, `execution_authority=false`, and `credentials_used=false` unless Builder scope is explicitly changed in future docs and tests.

## Segment completion guard — PMBT/QuantDinger adoption slice

**Added:** 2026-05-26 10:27:08Z

Preserve these rules after the backtest-center adoption slice:

- `BacktestArtifactRef` must continue to reject local `file://` project artifacts, traversal, missing checksums, and missing media types.
- Fixture artifact refs must remain `fixture_dev_only`; do not use them as promotion-grade evidence.
- Manifest-backed datasets must reference Builder-owned manifest artifacts, not arbitrary remote URLs.
- Strategy module registry entries are metadata-only and allowlisted; do not import arbitrary strategy module paths from user input.
- Research/optimizer jobs remain `offline_research`, `manual_promotion_required=true`, `may_submit_order=false`, and `execution_authority=false`.
- Results UI can show metrics/report/chart metadata, but must not add deploy/live/submit-order controls.

## 20. Standalone Builder platform / ND decoupling guard

Nautilus Builder is now the open-source standalone product. Nautilus-Daedalus is private/personal reference only.

- Do not import Nautilus-Daedalus modules, migrations, or runtime internals into Builder.
- Do not require `DAEDALUS_REPO_PATH` or an ND checkout for Builder startup, tests, migrations, or web/API operation.
- Clean-room adoption is allowed: architecture patterns, table categories, event-flow concepts, and safety gates may be re-expressed as Builder-owned contracts.
- Keep PostgreSQL as control-plane/audit/metadata. Keep market data, Nautilus catalog data, equity curves, orders/fills/positions frames, and heavy backtest artifacts in Parquet/catalog/artifact storage.
- Keep Redis/event streams as runtime fan-out/status transport, not permanent truth.
- Existing Builder authoring/backtest/research/promotion UI paths remain no-live-authority and must keep `may_submit_order=false`.
- Paper mode may represent simulated execution only and must not use live broker credentials.
- Live mode is disabled by default and requires all of: `runtime_mode='live'`, enabled profile, server-side credential slot reference, risk profile, manual review, reconciliation, activation identity/time, config checksum, `live_trading_enabled=true`, `execution_authority=true`, and `may_submit_order=true`.
- No browser-side API keys, exchange credentials, or live execution toggles.
- Telegram remains notification/approval UX unless a later segment explicitly adds a tested backend approval command path; Telegram must not own execution truth.
- AI continuous improvement remains advisory until a human/manual promotion package is approved and backend runtime gates accept it.

Minimum regression commands:

```bash
rtk pytest tests/infrastructure/test_builder_standalone_platform_migration.py -q
python3 -m compileall -q packages services tests
```

Segment PLATFORM-1 evidence:

```bash
rtk pytest tests/infrastructure/test_builder_standalone_platform_migration.py -q
# RED before migration: 0 passed, 6 failed because 002 migration did not exist
# GREEN after migration: 6 passed
```

Segment PLATFORM-1 final evidence refresh:

```bash
git diff --check
rtk pytest tests/infrastructure/test_builder_standalone_platform_migration.py -q
python3 -m compileall -q packages services tests
rtk pytest tests/strategy_spec tests/strategy_validation tests/adapter_registry tests/instrument_registry tests/strategy_compiler tests/backtest_jobs tests/runtime_events tests/backtest_runner tests/catalog_datasets tests/research_jobs tests/lifecycle tests/strategy_registry tests/promotions tests/web tests/ai_builder tests/integration tests/workflow_spine tests/auth tests/api tests/infrastructure -q
cd apps/web && npm run typecheck && npm test && npm run build && npm run test:e2e
cd apps/web && npm audit --omit=dev --audit-level=high
# diff check passed; infra migration tests 6 passed; targeted Python suite 316 passed; Vitest 21 passed; Playwright 4 passed; audit high exited 0 with only existing moderate Next/PostCSS advisory.
```

PostgreSQL syntax evidence:

```bash
docker run postgres:16-alpine ...
psql -U postgres -d nautilus_builder -v ON_ERROR_STOP=1 -f /tmp/001.sql -f /tmp/002.sql
# 001 + 002 migrations applied successfully in a disposable PostgreSQL 16 container
```

## 21. Standalone execution lane guard

Builder execution must stay decoupled from strategy authoring/research lanes.

- Execution lane consumes explicit `ExecutionLaneCommand` records, not live strategy process objects.
- Execution worker code must not import `packages.strategy_*`, `packages.nautilus_rule_graph.strategy`, or user strategy modules.
- `strategy_lane_coupled` must remain `false` on execution lane profiles, commands, reports, and heartbeats.
- Paper execution lane is simulated only: `may_submit_order=false`, `live_trading_enabled=false`, no live credentials.
- Live execution lane remains disabled by default and needs profile + command gates: manual approval, risk profile, credential slot ref, reconciliation, activation identity/time, config checksum, and approved risk decision.
- Do not store raw exchange credentials in execution commands, reports, API payloads, or database rows. Store only server-side credential slot references.
- Execution reports are the execution evidence source; strategy/backtest events are not fill/order truth.
- Future Nautilus `LiveNode` / adapter submission work must build on this lane contract and add ExecTester/reconciliation evidence before live-readiness claims.

Minimum regression commands:

```bash
rtk pytest tests/execution_lane tests/api/test_execution_lane_routes.py tests/infrastructure/test_builder_execution_lane_migration.py -q
python3 -m compileall -q packages services tests
```

Segment EXEC-1 evidence:

```bash
git diff --check
rtk pytest tests/execution_lane tests/api/test_execution_lane_routes.py tests/infrastructure/test_builder_execution_lane_migration.py -q
python3 -m compileall -q packages services tests
rtk pytest tests/strategy_spec tests/strategy_validation tests/adapter_registry tests/instrument_registry tests/strategy_compiler tests/backtest_jobs tests/runtime_events tests/backtest_runner tests/catalog_datasets tests/research_jobs tests/execution_lane tests/lifecycle tests/strategy_registry tests/promotions tests/web tests/ai_builder tests/integration tests/workflow_spine tests/auth tests/api tests/infrastructure -q
cd apps/web && npm run typecheck && npm test && npm run build && npm run test:e2e
cd apps/web && npm audit --omit=dev --audit-level=high
psql -U postgres -d nautilus_builder -v ON_ERROR_STOP=1 -f /tmp/001.sql -f /tmp/002.sql -f /tmp/003.sql
# focused tests 10 passed; targeted Python suite 326 passed; Vitest 21 passed; Playwright 4 passed; audit high exited 0; migrations 001-003 applied in disposable PostgreSQL 16.
```

Execution lane worker smoke:

```bash
python3 -m services.workers.execution_lane_worker --runtime-profile-id rp_paper_001 --worker-id exec_worker_smoke
# emitted execution_lane JSON with strategy_lane_coupled=false and may_submit_order=false
```

## 22. Execution lane venue/UI feature guard

Execution lane profiles and commands must be venue-bound before any worker or UI treats them as active.

- Enabled execution profiles require `adapter_id` and `venue`.
- Commands must match the profile's tenant, project, lane mode, adapter ID, venue, and optional venue account ID before enqueueing.
- Execution status payloads may expose `venue_bindings` and `ui_features`, but `credential_inputs_allowed` must remain `false`.
- Browser UI can show/hide execution lane, paper-control, and live-control surfaces from backend flags only. Do not add exchange secret, password, private-key, or signing-material inputs.
- Paper controls are simulated-only and must not set `may_submit_order`, `execution_authority`, or `live_trading_enabled`.
- Live controls require full live authority gates: live mode, enabled profile, manual review, reconciliation, risk profile, server-side credential slot, activation identity/time, config checksum, `live_trading_enabled=true`, `execution_authority=true`, and `may_submit_order=true`.
- Venue binding does not prove real adapter connectivity. Future Nautilus `LiveNode`/adapter work still needs ExecTester/reconciliation evidence and explicit live-readiness review.

Minimum regression commands:

```bash
rtk pytest tests/execution_lane tests/api/test_execution_lane_routes.py tests/api/test_execution_lane_venue_features.py tests/web/test_execution_lane_ui_contract.py tests/infrastructure/test_builder_execution_lane_venue_migration.py -q
cd apps/web && npm run typecheck && npm test && npm run build && npm run test:e2e
```

Segment EXEC-2 evidence:

```bash
git diff --check
rtk pytest tests/execution_lane tests/api/test_execution_lane_routes.py tests/api/test_execution_lane_venue_features.py tests/web/test_execution_lane_ui_contract.py tests/infrastructure/test_builder_execution_lane_venue_migration.py -q
python3 -m compileall -q packages services tests
rtk pytest tests/strategy_spec tests/strategy_validation tests/adapter_registry tests/instrument_registry tests/strategy_compiler tests/backtest_jobs tests/runtime_events tests/backtest_runner tests/catalog_datasets tests/research_jobs tests/execution_lane tests/lifecycle tests/strategy_registry tests/promotions tests/web tests/ai_builder tests/integration tests/workflow_spine tests/auth tests/api tests/infrastructure -q
cd apps/web && npm run typecheck && npm test && npm run build && npm run test:e2e
cd apps/web && npm audit --omit=dev --audit-level=high
psql -U postgres -d nautilus_builder -v ON_ERROR_STOP=1 -f /tmp/001.sql -f /tmp/002.sql -f /tmp/003.sql -f /tmp/004.sql
# focused tests 17 passed; targeted Python suite 334 passed; Vitest 21 passed; Playwright 4 passed; high audit gate exited 0; migrations 001-004 applied in disposable PostgreSQL 16.
```

## 23. Sectioned operator UI guard

The Builder UI is now organized as a compact seven-section operator workflow. Preserve the section boundaries:

1. Dashboard / Home
2. AI Strategy Builder
3. StrategySpec Editor
4. Market + Dataset Setup
5. Backtest Center
6. Results / Research
7. Execution Lane / Config

Guardrails:

- The Dashboard may describe order authority in user-friendly terms, but should not embed raw `submit_order` or `TradeAction` strings. Keep raw promotion evidence strings in `PromotionRequestPanel` or backend/API tests.
- AI Strategy Builder remains prompt/StrategySpec drafting only. It must not run backtests or promotion automatically.
- StrategySpec Editor must keep block/canvas/inspector/spec-preview roles visible and must say backend validation is required.
- Market + Dataset Setup must keep adapter/venue, instrument search, dataset profile, and catalog guard visible without browser credential inputs or credential-copy drift.
- Backtest Center may show `may_submit_order: false` as evidence, but it must remain an observational terminal/status/artifact surface.
- Results / Research may show metric cards and chart placeholders; do not add deploy/live/submit-order controls.
- Execution Lane / Config may show backend feature flags and venue bindings only. Paper/live controls are visibility-only in the browser.
- Do not add new UI dependencies for charts or editors without an explicit segment, TDD coverage, and security/readiness review.

Minimum regression commands:

```bash
pytest tests/web/test_sectioned_operator_ui.py tests/web/test_execution_lane_ui_contract.py tests/web/test_app_shell_contract.py tests/web/test_antd_operator_ui_contract.py tests/web/test_promotion_frontend.py tests/web/test_results_dashboard_frontend.py tests/web/test_frontend_data_wiring.py tests/web/test_ai_copilot_frontend.py -q
cd apps/web && npm test -- --run components/dashboard/BuilderDashboard.test.tsx components/ai-builder/AiStrategyCopilot.test.tsx components/strategy-builder/StrategyBuilderWorkspace.test.tsx components/market/MarketProfilePanel.test.tsx components/results/ResultsDashboard.test.tsx components/config/ModelConfigTabs.test.tsx
```

Segment UI-SECTIONS-1 focused evidence:

```bash
pytest tests/web/test_sectioned_operator_ui.py -q
# 7 passed

pytest tests/web/test_sectioned_operator_ui.py tests/web/test_execution_lane_ui_contract.py tests/web/test_app_shell_contract.py tests/web/test_antd_operator_ui_contract.py tests/web/test_promotion_frontend.py tests/web/test_results_dashboard_frontend.py tests/web/test_frontend_data_wiring.py tests/web/test_ai_copilot_frontend.py -q
# 25 passed

cd apps/web && npm test -- --run components/dashboard/BuilderDashboard.test.tsx components/ai-builder/AiStrategyCopilot.test.tsx components/strategy-builder/StrategyBuilderWorkspace.test.tsx components/market/MarketProfilePanel.test.tsx components/results/ResultsDashboard.test.tsx components/config/ModelConfigTabs.test.tsx
# 6 files / 9 tests passed
```

Segment UI-SECTIONS-1 final evidence:

```bash
git diff --check
python3 -m compileall -q packages services tests
rtk pytest tests/strategy_spec tests/strategy_validation tests/adapter_registry tests/instrument_registry tests/strategy_compiler tests/backtest_jobs tests/runtime_events tests/backtest_runner tests/catalog_datasets tests/research_jobs tests/execution_lane tests/lifecycle tests/strategy_registry tests/promotions tests/web tests/ai_builder tests/integration tests/workflow_spine tests/auth tests/api tests/infrastructure -q
cd apps/web && npm run typecheck && npm test && npm run build && npm run test:e2e
cd apps/web && npm audit --omit=dev --audit-level=high
# diff/compile passed; targeted Python suite 341 passed; Vitest 22 passed; Playwright 4 passed; high audit gate exited 0 with only existing moderate Next/PostCSS advisory.
```

## 24. NautilusTrader backend dependency guard

NautilusTrader must remain an upstream Python package dependency for Builder backend code.

- Keep `nautilus_trader` installed through the backend Python dependency manifest (`pyproject.toml` / lock), not vendored into this repository.
- Backend code may import official NautilusTrader modules directly for Strategy, BacktestEngine/BacktestNode, ParquetDataCatalog, model data, test-kit smoke, adapter contracts, and live/runtime seams.
- Structure backend packages around NautilusTrader concepts first: strategy/spec compilation, data catalogs, backtest runner, adapter registry, execution lane, runtime events, promotions/evidence, and live-readiness gates.
- Use Nautilus-Daedalus as reference architecture only. Clean-room adopt useful boundaries; do not import ND modules, require `DAEDALUS_REPO_PATH`, or copy private runtime internals.
- Before claiming NT runtime readiness, verify the active environment imports the pinned package version and at least the real-engine/catalog smoke tests pass.

Minimum regression commands:

```bash
python3 - <<'PY'
import importlib.metadata as md
import nautilus_trader
print(md.version('nautilus_trader'), getattr(nautilus_trader, '__version__', 'unknown'))
PY
rtk pytest tests/backtest_runner/test_runtime_dependency_check.py tests/backtest_runner/test_real_nautilus_engine_smoke.py tests/backtest_runner/test_strategy_spec_catalog_replay.py -q
```


## 25. Headless backend runtime guard

Builder backend readiness must not depend on the web UI or the private Nautilus-Daedalus checkout.

- Keep a backend-only diagnostic surface in `packages/backend_runtime` / `services.backend_runtime`.
- Preserve `web_ui_required=false` and `nautilus_daedalus_required=false` in the headless runtime report unless the product direction explicitly changes.
- Keep `services.api.dev_server` dependency-free for local contract checks.
- Run the production-style FastAPI app through the project dependency environment (`uv run uvicorn 'services.api.fastapi_app:create_fastapi_app' --factory ...`).
- Keep execution-lane worker entrypoints separate from strategy authoring modules; worker scaffold output must keep `strategy_lane_coupled=false` and `may_submit_order=false`.
- Do not add imports from `apps/web`, `nautilus_actors`, `nautilus_runtime`, `nautilus_strategies`, `nautilus_brain`, or `nautilus_adapters` into backend runtime checks.
- NautilusTrader remains the pinned upstream Python dependency and must be checked with `check_nautilus_runtime_version()`.

Minimum regression commands:

```bash
rtk pytest tests/integration/test_headless_backend_runtime.py -q
python3 -m services.backend_runtime --runtime-profile-id rp_paper_001
uv run python -c "from services.api.fastapi_app import create_fastapi_app; app=create_fastapi_app(); print(app.title, len(app.routes))"
python3 -m services.workers.execution_lane_worker --runtime-profile-id rp_paper_001 --worker-id exec_worker_smoke
```

Segment HEADLESS-BACKEND-1 focused evidence:

```bash
rtk pytest tests/integration/test_headless_backend_runtime.py -q
# 6 passed
```


Segment HEADLESS-BACKEND-1 final evidence:

```bash
git diff --check
python3 -m compileall -q packages services tests
rtk pytest tests/integration/test_headless_backend_runtime.py tests/api/test_fastapi_app.py tests/api/test_route_mounts.py tests/execution_lane tests/backtest_runner/test_runtime_dependency_check.py tests/backtest_runner/test_real_nautilus_engine_smoke.py -q
rtk pytest tests/strategy_spec tests/strategy_validation tests/adapter_registry tests/instrument_registry tests/strategy_compiler tests/backtest_jobs tests/runtime_events tests/backtest_runner tests/catalog_datasets tests/research_jobs tests/execution_lane tests/lifecycle tests/strategy_registry tests/promotions tests/web tests/ai_builder tests/integration tests/workflow_spine tests/auth tests/api tests/infrastructure -q
uv run nautilus-builder-backend-check --runtime-profile-id rp_paper_001
cd apps/web && npm run typecheck && npm test && npm run build && npm run test:e2e
cd apps/web && npm audit --omit=dev --audit-level=high
# diff/compile passed; focused Python 38 passed; full Python 347 passed; backend check emitted no web/Daedalus imports and pinned NT match; Vitest 22 passed; Playwright 4 passed; high audit gate exited 0 with only existing moderate Next/PostCSS advisory.
```


## 26. Deep review guardrails — NT/AI/backend alignment (2026-05-26)

These guards are active until the 2026-05-26 deep-review findings are closed with tests and runtime evidence.

### StrategySpec validation guard

- Do not claim AI-generated StrategySpecs are safe just because Pydantic validation passes.
- Add/maintain tests proving:
  - `validation.requires_backtest_before_shadow` must be `true`.
  - `data_range.start` and `data_range.end` parse as datetimes and `start < end`.
  - rule operators have exact, supported arity.
  - rule operands reference known indicators/fields/constants.
  - safe enum values such as `created_from="imported"` are not rejected by raw-code substring checks.

Minimum regression target:

```bash
rtk pytest tests/strategy_validation tests/strategy_spec -q
python3 - <<'PY'
from tests.strategy_spec.test_schema_valid import make_valid_spec
from packages.strategy_validation.validators import validate_strategy_spec
spec = make_valid_spec()
spec['validation']['requires_backtest_before_shadow'] = False
assert not validate_strategy_spec(spec).is_valid
PY
```

### Nautilus backtest semantics guard

- Treat `run_strategy_spec_catalog_replay()` as NT catalog/runtime smoke until `RuleGraphBacktestStrategy` evaluates indicators, rules, and risk from the StrategySpec.
- Do not use zero-order/zero-position replay output as proof of strategy profitability, rule correctness, or promotion readiness.
- Before stronger backtest claims, add evidence that StrategySpec rules produce deterministic signal/position/order-intent observations under Nautilus replay without live order authority.

Minimum regression target:

```bash
rtk pytest tests/backtest_runner/test_strategy_spec_catalog_replay.py tests/backtest_runner/test_catalog_backed_nautilus_replay_smoke.py -q
# plus new tests proving rule/indicator evaluation, not only quote-tick observation
```

### FastAPI/web auth guard

- Protected FastAPI routes require bearer auth; frontend API helpers must either propagate a valid auth context or present a clear local-dev mode.
- Do not claim web/API integration is fixed from mocked component tests alone.
- Any VM deployment using FastAPI must verify the browser-to-Next-proxy-to-FastAPI path with an actual token.

Minimum regression target:

```bash
rtk pytest tests/api/test_fastapi_app.py -q
cd apps/web && npm test -- --run lib/api.test.ts
# plus an e2e/proxy test that proves Authorization reaches FastAPI for /api/strategies and /api/ai-builder/draft
```

### Dependency-free API exposure guard

- `services.api.dev_server` is a local contract server, not a production server.
- Do not recommend `--host 0.0.0.0` for `services.api.dev_server` unless the surrounding text says it is unsafe without a private network/proxy and must not be internet exposed.
- Production/staging examples should prefer the FastAPI entrypoint with auth middleware/session propagation.

### Database guard

- Do not call `PostgresWorkflowRepository` production Postgres-ready while it uses `sqlite3.Connection` or SQLite `insert or replace` SQL.
- Keep runtime storage names honest: SQLite/in-memory contract repositories are acceptable for tests/demo, but production DB claims require psycopg-backed implementation against `infra/migrations`.

Minimum regression target:

```bash
rtk pytest tests/workflow_spine tests/infrastructure -q
# plus real psycopg/Postgres integration or rename the current SQLite contract repository
```

### Artifact/evidence guard

- Strict promotion evidence must use scoped `artifact://builder/...` refs with checksums and compile/version binding.
- Do not feed `artifact://backtests/...` or `fixture://...` refs into production promotion paths.
- Keep fixture fallback gated as dev-only and visibly labeled.

### AI improvement lane guard

- OpenAI-compatible provider use is advisory-only: no shell, credentials, broker/exchange calls, `submit_order`, or `TradeAction` in prompts/specs/audit output.
- Default production AI audit must be durable; in-memory `RecordedAiDraftStore` is test/demo only.
- EvoMap/LangGraph-style continuous improvement claims require durable state/checkpoints, prompt-response metadata, accepted/rejected decisions, and replayable improvement-cycle IDs.

### Segment DR-CLOSURE-1 regression guard — StrategySpec validation

Keep these tests green whenever StrategySpec schema, AI draft output, or validation policy changes:

```bash
rtk pytest tests/strategy_validation/test_deep_review_closure_validation.py tests/strategy_validation tests/strategy_spec tests/ai_builder -q
```

Do not reintroduce substring-only raw-code checks that reject `created_from="imported"`, and do not allow `requires_backtest_before_shadow=false` to pass Builder validation.

### Segment DR-CLOSURE-2 regression guard — no-order rule replay

StrategySpec replay may evaluate signals/rules, but Builder backtest/research paths must remain no-order unless a separate approved live-execution lane owns the authority.

Keep this regression target green:

```bash
rtk pytest tests/nautilus_rule_graph tests/backtest_runner/test_strategy_spec_catalog_replay.py -q
```

Required invariants: `strategy_logic_evaluated=true`, `signal_observation_count` is populated, `order_intent_count=0`, `orders=0`, `positions=0`, `execution_authority=false`, and `may_submit_order=false`.

### Segment DR-CLOSURE-3 regression guard — web/API auth and local dev server

Protected FastAPI routes must keep requiring bearer auth. Browser/VM demos may use a configured local token, but Builder must not add browser credential fields or silently downgrade protected routes to anonymous access.

Regression target:

```bash
cd apps/web && npm run typecheck && npm test -- --run lib/api.test.ts
rtk pytest tests/api/test_fastapi_app.py tests/integration/test_readme_readiness_hygiene.py tests/integration/test_headless_backend_runtime.py -q
```

Do not document `services.api.dev_server --host 0.0.0.0`; it is dependency-free and unauthenticated by design.

### Segment DR-CLOSURE-4 regression guard — evidence lineage, roots, and durable audit

Keep the medium-risk closure suite green whenever registry, job lineage, artifact refs, catalog datasets, AI audit, or workflow storage changes:

```bash
rtk pytest tests/catalog_datasets tests/api/test_backtest_job_routes.py tests/api/test_fastapi_app.py tests/backtest_jobs tests/backtest_runner/test_result_normalizer.py tests/strategy_registry tests/workflow_spine tests/ai_builder -q
```

Required invariants:

- strict backtest jobs require a real 64-character hex `compile_hash` and keep `compile_artifact_id` separate;
- non-fixture result artifacts use scoped `artifact://builder/{project_id}/{user_id}/...` refs;
- catalog dataset registration/selection requires a root policy unless explicitly in test compatibility mode;
- production FastAPI startup must not silently fall back to in-memory AI audit storage;
- `SqliteWorkflowRepository` is the honest name for the current SQLite contract implementation; do not cite the compatibility `PostgresWorkflowRepository` alias as production Postgres evidence.

### Master regression guard — deep-review closure 2026-05-26

Before any future commit that claims Builder NT readiness, run at minimum:

```bash
git diff --check
python3 -m compileall -q packages services tests
rtk pytest tests/strategy_spec tests/strategy_validation tests/adapter_registry tests/instrument_registry tests/strategy_compiler tests/backtest_jobs tests/runtime_events tests/backtest_runner tests/catalog_datasets tests/research_jobs tests/execution_lane tests/lifecycle tests/strategy_registry tests/promotions tests/web tests/ai_builder tests/integration tests/workflow_spine tests/auth tests/api tests/infrastructure -q
cd apps/web && npm run typecheck && npm test && npm run build
```

Do not weaken these permanent boundaries:

- Builder authoring/replay paths do not call `submit_order`, create `TradeAction`, or collect broker/browser credentials.
- `/home/mok/projects/Nautilus-Daedalus` remains reference-only for Builder work unless the user explicitly changes target.
- NautilusTrader runtime/backtest claims must distinguish no-order catalog/rule evaluation evidence from live/paper trading execution evidence.

## Segment 2026-05-26-1 completion guard — UI StrategySpec serialization

Segment 2026-05-26-1 is complete. Preserve these rules going forward:

- `graphToStrategySpec()` must remain backend StrategySpec-shaped: schema/version, adapter/venue/instrument, data_range, indicators, rules, risk, validation, and provenance are required.
- Do not reintroduce `graph_edges` into the serialized StrategySpec payload unless the backend schema explicitly supports it.
- UI graph defaults must stay `signal_preview_only` and draft-only; backend validation remains required before backtest creation.
- `strategySpecToGraph()` must keep reading canonical object-shaped `indicators` so backend drafts remain editable.

Segment evidence:

```bash
cd apps/web && npm test -- --run lib/strategySpec.test.ts
# 3 passed after RED/GREEN cycle
```

## Segment 2026-05-26-2 completion guard — Backtest Center runtime rendering

Segment 2026-05-26-2 is complete. Preserve these rules going forward:

- `/backtests/[jobId]` must call backend job and event contracts before presenting job state.
- Backtest artifacts are refs/manifests only; the UI must not treat them as live execution handles.
- The only browser-side control is request-cancel. Do not add shell, worker mutation, or order submission controls.
- Keep `may_submit_order: false` or equivalent visible on the Backtest Center route.

Segment evidence:

```bash
cd apps/web && npm test -- --run app/backtests/'[jobId]'/page.test.tsx
# 1 passed after RED/GREEN cycle
```

## Segment 2026-05-26-3 completion guard — Dashboard navigation and builder route

Segment 2026-05-26-3 is complete. Preserve these rules going forward:

- Dashboard workflow CTAs must navigate/switch visible Builder sections; do not leave primary CTA buttons inert.
- Strategy detail `Open in Builder` links must point to an implemented route.
- `/builder/[strategyId]` remains a draft-only strategy-context route; do not add live order controls or credential fields there.

Segment evidence:

```bash
cd apps/web && npm test -- --run components/dashboard/BuilderDashboard.test.tsx app/builder/'[strategyId]'/page.test.tsx
# 3 passed after RED/GREEN cycle
```

## Segment 2026-05-26-4 completion guard — LLM config and AI lineage UX

Segment 2026-05-26-4 is complete. Preserve these rules going forward:

- `/api/config/llm` may persist non-secret provider/model-role config only; browser payloads containing API keys, secrets, authorization headers, or tokens must be rejected.
- UI config may expose `OPENAI_BASE_URL` and model role names, but never API key inputs.
- Secrets storage remains `server_environment`.
- AI copilot lineage/version identifiers stay hidden by default and must not overwhelm the primary natural-language strategy prompt workflow.

Segment evidence:

```bash
rtk pytest tests/api/test_llm_config_routes.py -q
# 2 passed
cd apps/web && npm test -- --run components/config/ModelConfigTabs.test.tsx components/ai-builder/AiStrategyCopilot.test.tsx
# 3 passed
```

## Master reconciliation guard — 2026-05-26 UI workflow closure

The 2026-05-26 UI closure baseline is verified. Preserve these stop conditions:

- Graph-built StrategySpecs must stay backend-shaped and `signal_preview_only` until backend validation accepts them.
- Backtest Center must read backend contracts and remain observational/cancel-request only, including degraded fallback state for missing dev fixture jobs.
- Dashboard CTAs and strategy detail links must keep routing operators into real Builder sections/routes.
- `/api/config/llm` must reject browser secrets and persist only non-secret provider/model role config.
- AI lineage IDs must stay hidden from the default user workflow and available only under Advanced controls.
- Do not add `submit_order`, `TradeAction`, browser credential inputs, or live/paper execution authority to these UI paths.

Master evidence:

```bash
git diff --check
# passed
python3 -m compileall -q packages services tests
rtk pytest tests/strategy_spec tests/strategy_validation tests/adapter_registry tests/instrument_registry tests/strategy_compiler tests/backtest_jobs tests/runtime_events tests/backtest_runner tests/catalog_datasets tests/research_jobs tests/execution_lane tests/lifecycle tests/strategy_registry tests/promotions tests/web tests/ai_builder tests/integration tests/workflow_spine tests/auth tests/api tests/infrastructure -q
# 365 passed
cd apps/web && npm run typecheck && npm test && npm run build && npm run test:e2e
# typecheck passed; 29 Vitest tests passed; Next build passed; 4 Playwright tests passed
```

## Segment 2026-05-26-5 completion guard — Backtest launch manifest

Segment 2026-05-26-5 is complete. Preserve these rules going forward:

- Dashboard workflow tab `3. Backtest` must remain a backend job-manifest launcher plus observational terminal, not a browser-owned worker or shell surface.
- Backtest job creation from the UI must include strategy version, validation report, compile hash, adapter profile, instrument, dataset ID, data range, data type, timeframe, and market type.
- `compile_hash` must remain gated to a 64-character SHA-256 shape before `/api/backtest-jobs` is called from the UI.
- The UI may link to `/backtests/{job_id}` after backend job creation, but must not add browser credentials, live/paper execution authority, worker mutation controls, or automatic promotion.

Segment evidence:

```bash
cd apps/web && npm test -- --run components/backtests/BacktestLaunchPanel.test.tsx components/dashboard/BuilderDashboard.test.tsx
# 5 passed after RED/GREEN cycle
```

## Segment guard — BacktestNode execution trigger

Backtest execution must remain backend-owned:

- UI/browser may request `POST /api/backtest-jobs/{job_id}/run`, but it must not supply StrategySpec payloads, catalog paths, worker commands, credentials, or shell instructions for execution.
- The backend must resolve the saved `StrategySpec` from `strategy_version_id`, recompute the backtest `compile_hash`, select the registered project-scoped `CatalogDataset`, and pass the registry-owned `catalog_root` into Nautilus replay.
- A run may proceed only when the selected dataset is under the configured catalog root and belongs to the authenticated user/project scope.
- BacktestNode remains the main historical/repeatable testing lane.
- TradingNode paper remains a separate execution-lane gate after backtest evidence and manual promotion review.
- Result artifacts must be persisted under `artifact://builder/{project_id}/{user_id}/...` and referenced from the job; do not fabricate result refs.
- FastAPI backtest event replay must require bearer auth and job project scope before returning worker events or artifact metadata.
- Keep no-order invariants: StrategySpec replay artifacts must preserve `execution_authority == false`, `credentials_used == false`, `orders == 0`, and `positions == 0` for Builder signal-preview/backtest evidence.

Minimum regression coverage for this segment:

```bash
rtk pytest tests/api/test_backtest_job_execution_routes.py tests/backtest_runner/test_worker_integration.py tests/backtest_runner/test_strategy_spec_catalog_replay.py -q
```

## Segment guard — TradingNode paper/live execution lane

TradingNode paper/live work must preserve these boundaries:

- Keep execution lane separate from StrategySpec authoring and BacktestNode historical replay.
- Python `nautilus_trader.live.node.TradingNode` usage must be labeled `python_live_integration_specific`; do not present it as the Rust v2 `LiveNode` path.
- Paper execution plans use `runtime_environment=sandbox`, `live_trading_enabled=false`, `execution_authority=false`, `may_submit_order=false`, and no credential slot.
- Live execution plans may set `may_submit_order=true` only when all gates are present:
  - enabled live profile
  - `advisory_only=false`
  - manual review required and `manual_review_id`
  - risk profile ID and approved command risk decision
  - server-side `credential_slot_ref`
  - activation identity/time
  - config checksum
  - DataTester evidence ref
  - ExecTester evidence ref
  - reconciliation evidence ref
  - `live_trading_enabled=true`
  - `execution_authority=true`
- Browser/UI payloads must never carry API keys, private keys, passwords, authorization tokens, or raw credentials.
- Worker reports may emit `tradingnode_runtime_plan` evidence but must not start real venue connectivity in contract tests.
- Do not import or depend on Nautilus-Daedalus runtime internals from Builder; ND remains a read-only reference.
- Real venue paper/live readiness cannot be claimed until adapter-specific DataTester, ExecTester, reconciliation, and operator approval evidence exists and command evidence refs match the active runtime profile.

Minimum regression coverage for this segment:

```bash
rtk pytest tests/execution_lane/test_tradingnode_runtime_contract.py tests/api/test_execution_lane_tradingnode_routes.py -q
rtk pytest tests/execution_lane tests/api/test_execution_lane_routes.py tests/api/test_execution_lane_venue_features.py tests/api/test_execution_lane_tradingnode_routes.py tests/infrastructure -q
```

## Segment guard — Execution lane full web wire

The `/config` execution-lane UI may orchestrate only this paper/sandbox contract sequence:

```text
register paper profile -> fetch runtime plan -> enqueue paper command -> backend worker run-once -> display report
```

Preserve these rules:

- The browser may not collect API keys, private keys, passwords, authorization tokens, raw credentials, shell commands, worker process handles, or venue signing material.
- The browser may not expose a `Submit order` / `Cancel order` / `Modify order` action. It may enqueue a paper execution-lane command request only after a backend runtime plan is READY.
- `POST /api/execution-lane/worker/run-once` must remain a backend-owned local/dev worker seam; it may emit a `tradingnode_runtime_plan` report but must not start real venue connectivity in contract tests.
- Paper runtime plans must keep `runtime_environment=sandbox`, `live_trading_enabled=false`, `execution_authority=false`, `may_submit_order=false`, `browser_credentials_allowed=false`, and `credential_inputs_allowed=false`.
- UI text must keep the authority boundary visible: no browser credentials, backend worker only, paper sandbox only, and no strategy-lane coupling.
- Live mode must remain unavailable from this browser wire unless all live execution-lane gates in the previous TradingNode guard are satisfied and reviewed.
- Keep `python_live_integration_specific` labeling for Python `TradingNode`; do not rename it into a universal `LiveNode` claim.

Minimum regression coverage:

```bash
rtk pytest tests/api/test_execution_lane_tradingnode_routes.py tests/web/test_execution_lane_ui_contract.py -q
cd apps/web && npm test -- --run components/config/ExecutionLaneFeaturePanel.test.tsx lib/api.test.ts components/dashboard/BuilderDashboard.test.tsx
cd apps/web && npm run typecheck
```

### Master reconciliation guard — Execution lane full web wire

This segment is considered complete only while the following remains true:

- The UI shows the paper wire as sandbox/backend-worker-only.
- `runExecutionLaneWorkerOnce()` exists only as an API helper to a backend route; the browser never starts a process or opens a shell.
- Contract tests assert no API-key field and no submit-order button in the UI.
- Python and frontend verification continue to pass with the execution-lane route, API wrappers, and component test included.

Evidence captured for this closure:

```bash
rtk pytest tests/api/test_execution_lane_tradingnode_routes.py tests/api/test_execution_lane_routes.py tests/api/test_execution_lane_venue_features.py tests/execution_lane tests/web/test_execution_lane_ui_contract.py -q
# 26 passed
cd apps/web && npm test -- --run components/config/ExecutionLaneFeaturePanel.test.tsx lib/api.test.ts components/dashboard/BuilderDashboard.test.tsx
# 12 passed
```

## Segment guard — BacktestNode web run full wire

The `Run BacktestNode` UI action must preserve the backend-owned execution boundary:

- The browser may call only `POST /api/backtest-jobs/{job_id}/run` for an already-created backend job.
- The browser payload for run must remain empty; do not add StrategySpec JSON, catalog paths, worker image/name overrides, shell commands, credentials, API keys, private keys, or venue credentials.
- UI may display returned job state, runtime events, artifact refs, and replay evidence flags, but it must not mutate worker state directly or fabricate artifacts.
- The backend remains responsible for StrategySpec lookup, compile-hash recomputation, catalog dataset selection, catalog-root policy, artifact persistence, and event emission.
- Keep BacktestNode as historical/repeatable evidence only. Do not route TradingNode paper/live controls through this panel.
- Preserve no-order evidence display: `orders: 0`, `positions: 0`, `execution_authority: false`, and `credentials_used: false` for Builder signal-preview/catalog replay evidence.
- Manual promotion review remains required before any paper/live execution-lane work.

Minimum regression coverage for this segment:

```bash
cd apps/web && npm test -- --run components/backtests/BacktestLaunchPanel.test.tsx lib/api.test.ts
rtk pytest tests/web/test_frontend_data_wiring.py tests/web/test_sectioned_operator_ui.py -q
rtk pytest tests/api/test_backtest_job_execution_routes.py tests/backtest_runner/test_worker_integration.py tests/backtest_runner/test_strategy_spec_catalog_replay.py -q
```

### Master reconciliation guard — BacktestNode web run full wire

This segment is considered complete only while the following remains true:

- `runBacktestJob(jobId)` sends `POST /api/backtest-jobs/${jobId}/run` with `{}` only.
- `BacktestLaunchPanel` exposes `Run BacktestNode` only after a backend job exists and displays backend-returned events/artifact refs/result evidence.
- Frontend tests assert the create-job -> run-job sequence and no API-key / submit-order UI.
- Source-scan tests assert the run wrapper/route string and section surface.
- Backend regression tests for scoped BacktestNode replay, worker integration, and catalog replay keep passing.

Evidence captured for this closure:

```bash
rtk pytest tests/api/test_backtest_job_execution_routes.py tests/backtest_runner/test_worker_integration.py tests/backtest_runner/test_strategy_spec_catalog_replay.py -q
# 15 passed
cd apps/web && npm test -- --run components/backtests/BacktestLaunchPanel.test.tsx lib/api.test.ts
# 12 passed
```

## Segment guard — Execution credential-slot bootstrap

Credential bootstrap is allowed only under these constraints:

- The only browser credential entry surface is the local/dev **Credential slot bootstrap** form in `/config`.
- The UI may submit venue-prefixed credential variables to `POST /api/execution-lane/credential-slots` once, but it must clear secret fields after save and keep only the returned `credential_slot_ref`.
- The backend may write local/dev credentials only to `.env.execution.local` or an explicitly equivalent gitignored local env-file policy. Never commit `.env`, `.env.*`, or generated credential files.
- Credential-slot responses must not echo raw secret values. They may include `credential_slot_ref`, `redacted_keys`, `fingerprint`, `env_file_path`, `secrets_storage`, and `browser_secret_echo=false`.
- Runtime profile, command, StrategySpec, BacktestNode run, worker, and report payloads must not carry raw credentials, API secret values, passwords, private keys, authorization tokens, or browser shell/process handles.
- Builder-created `credslot://local-env/...` refs must be bound to matching tenant/project/runtime_profile/adapter/venue/lane_mode before profile registration. Externally managed `credslot://server/...` refs remain server-side operator references.
- Paper plans may bind a credential slot for sandbox/venue connectivity, but must keep `runtime_environment=sandbox`, `live_trading_enabled=false`, `execution_authority=false`, and `may_submit_order=false`.
- Live plans may bind a credential slot only with the existing live authority gates: manual review, risk profile, activated_by/at, config checksum, DataTester evidence, ExecTester evidence, reconciliation evidence, live authority, and approved command risk decision.
- Execution-lane worker reports may emit `risk_gate_status`, `credential_slot_bound`, and `secrets_storage`; they must not include secret values or claim a real venue-connected node was started in contract tests.

Minimum regression coverage:

```bash
rtk pytest tests/execution_lane/test_credential_slots.py tests/execution_lane/test_tradingnode_runtime_contract.py tests/api/test_execution_lane_credentials_routes.py tests/api/test_execution_lane_tradingnode_routes.py tests/web/test_execution_lane_ui_contract.py -q
cd apps/web && npm test -- --run components/config/ExecutionLaneFeaturePanel.test.tsx lib/api.test.ts
cd apps/web && npm run typecheck
```
