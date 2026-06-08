# Persistence Verification

This guide verifies that Builder state survives API restart when using
Postgres (`BUILDER_DATABASE_URL` set).

## Prerequisites

- Docker and Docker Compose
- The repo's `.env` file configured with a strong `BUILDER_API_TOKEN`

## Step 1: Start Services

```bash
# Start Postgres + API + Web
docker compose up -d postgres api web

# Wait for health checks
docker compose ps
```

## Step 2: Seed Demo Data

```bash
# The API auto-seeds demo data when BUILDER_SEED_DEMO_STRATEGIES=1
# Verify the strategies exist:
curl -s -H "Authorization: Bearer $BUILDER_API_TOKEN" \
  http://localhost:8000/api/strategies | python3 -m json.tool
```

You should see 8 demo strategies: `demo_draft`, `demo_validation_failed`,
`demo_validated`, `demo_compiled`, `demo_replay_failed`, `demo_replay_passed`,
`demo_promotion_requested`, `demo_promotion_ready`.

## Step 3: Record Evidence in Postgres

```bash
# Check that backtest jobs were persisted
curl -s -H "Authorization: Bearer $BUILDER_API_TOKEN" \
  http://localhost:8000/api/strategies/demo_replay_passed/evidence-summary | python3 -m json.tool
```

The response should show:
- `validation.status`: `"passed"`
- `compile.status`: `"passed"` with hash
- `replay.status`: `"passed"` with job refs
- `promotion.status`: `"missing"`

## Step 4: Restart the API

```bash
# Restart only the API service (Postgres stays up)
docker compose restart api

# Wait for it to come back
sleep 10
docker compose ps
```

## Step 5: Verify Persistence After Restart

```bash
# Strategy records still exist
curl -s -H "Authorization: Bearer $BUILDER_API_TOKEN" \
  http://localhost:8000/api/strategies | python3 -c "
import json, sys
data = json.load(sys.stdin)
strategies = data if isinstance(data, list) else data.get('strategies', [])
print(f'Strategies after restart: {len(strategies)}')
assert len(strategies) >= 8, 'Expected at least 8 strategies after restart'
print('OK: strategies persisted')
"

# Backtest evidence still exists
curl -s -H "Authorization: Bearer $BUILDER_API_TOKEN" \
  http://localhost:8000/api/strategies/demo_replay_passed/evidence-summary | python3 -c "
import json, sys
data = json.load(sys.stdin)
assert data['replay']['status'] == 'passed', f'Expected replay passed, got {data[\"replay\"][\"status\"]}'
assert len(data['replay']['jobs']) >= 1, 'Expected at least 1 replay job'
print('OK: backtest evidence persisted after restart')
"

# Promotion evidence still exists
curl -s -H "Authorization: Bearer $BUILDER_API_TOKEN" \
  http://localhost:8000/api/strategies/demo_promotion_ready/evidence-summary | python3 -c "
import json, sys
data = json.load(sys.stdin)
assert data['promotion']['status'] == 'ready', f'Expected promotion ready, got {data[\"promotion\"][\"status\"]}'
print('OK: promotion evidence persisted after restart')
"
```

## Step 6: Verify Direct Postgres Access

```bash
# Connect to Postgres and verify tables have data
docker compose exec postgres psql -U builder -d nautilus_builder -c "
SELECT 'strategies' as table_name, count(*) FROM builder.strategies
UNION ALL
SELECT 'strategy_versions', count(*) FROM builder.strategy_versions
UNION ALL
SELECT 'backtest_jobs', count(*) FROM builder.backtest_jobs
UNION ALL
SELECT 'backtest_results', count(*) FROM builder.backtest_results
UNION ALL
SELECT 'audit_events', count(*) FROM builder.audit_events
ORDER BY 1;
"
```

Expected: All tables have data (strategies >= 8, backtest_jobs > 0).

## Expected Results

After restart, all of the following must persist:
- ✅ Strategy records (`strategies`, `strategy_versions`)
- ✅ Backtest jobs (`backtest_jobs`)
- ✅ Compile artifact refs and hashes
- ✅ Replay/backtest refs and reports
- ✅ Promotion evidence and status
- ✅ Audit timeline events
- ✅ Builder config

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| Strategies disappear after restart | `BUILDER_DATABASE_URL` not set | Set env var, restart API |
| Backtest evidence missing after restart | Backtest jobs only in memory | Verify migration v4 applied |
| `relation "builder.backtest_jobs" does not exist` | Migration v4 not applied | Restart API (auto-applies migrations) |
| API warning: "in-memory repositories" | PG connection failed | Check `BUILDER_DATABASE_URL` and Postgres health |
