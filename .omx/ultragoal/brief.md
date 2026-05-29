# Nautilus Builder — MVP Completion Ultragoal

Clear all functional gaps 1-by-1 until the operator can go from strategy creation through backtest to execution lane in a single session.

## Stories

### G001: Strategy detail page with full spec, version history, and status timeline
- Rewrite `/strategies/[id]` page and `StrategyDetailClient` component
- Show full StrategySpec (indicators, rules, risk, validation) in readable AntD Descriptions
- Show version history table with version IDs and timestamps
- Show current status with colored chip and the lifecycle chain (draft → validated → backtested → approved → execution_ready)
- Add action buttons matching current status (Edit if draft/validated, Clone always, Backtest if eligible)
- Tests: typecheck + vitest component test

### G002: Backtest Center auto-fills manifest from selected strategy
- When operator selects a strategy in Backtest Center, auto-populate the BacktestLaunchPanel manifest fields (strategy_version_id, adapter_profile_id, instrument_id) from the strategy's spec
- Show selected strategy context above the launch panel
- Clear previous job results when a new strategy is selected
- Tests: typecheck + vitest

### G003: Execution Lane paper/shadow mode for approved strategies
- When an approved strategy is loaded into Execution Lane, wire it into the paper session start payload
- Show the attached strategy info (ID, status, instrument, adapter) in the session card
- The paper session start should reference the loaded strategy's version_id and lineage_id
- Tests: typecheck + vitest

### G004: Results/Reports page — browse real backtest results
- Replace hardcoded `res_001` with dynamic result listing
- Show list of available results with strategy name, date, and metrics summary
- Result detail page shows: key metrics (PnL, sharpe, drawdown), trade log table, artifact references
- Tests: typecheck + vitest

### G005: Fix 5 pre-existing vitest failures
- Fix `ExecutionLaneFeaturePanel.test.tsx` credential label mismatches (2 tests)
- Fix `app/builder/[strategyId]/page.test.tsx` missing Next.js router mock (1 test)
- Fix `BuilderDashboard.test.tsx` if any regressions from G001-G004
- All 42+ vitest tests must pass

### G006: Docker Compose for full stack
- Create `docker-compose.yml` at repo root
- Services: postgres (16-alpine), builder-api (FastAPI), web (Next.js)
- Postgres uses persistent volume
- API connects to Postgres, seeds demo data
- Web proxies API requests
- `docker compose up` brings everything up

### G007: Frontend auth integration
- Read `BUILDER_API_TOKEN` from env and attach as Bearer token to all API requests
- Add auth token to `apiClient.ts` / `api.ts` request headers
- Handle 401 responses gracefully (show auth error, don't crash)
- Login/logout not needed — token-based like current backend

### G008: Final quality gate
- Run ai-slop-cleaner on all changed files
- Rerun full verification (pytest 429+, vitest all green, tsc clean, npm build succeeds)
- Run $code-review on all changes
- Fix any review blockers
