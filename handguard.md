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
