# Local Verification Checklist

Run these commands before submitting changes. All must pass.

## Backend

```bash
# Lint
uv run ruff check .

# Tests
uv run pytest
```

## Frontend

```bash
cd apps/web

# Type checking
npm run typecheck

# Unit tests
npm test

# Production build
npm run build
```

## Safety Search

Verify no forbidden live-trading wording appears in frontend code:

```bash
grep -R "submit_order\|Start live trading\|live trading enabled\|Auto execute\|Guaranteed profit\|Auto trade now\|Deploy to exchange" \
  apps/web/src apps/web/components apps/web/lib --include='*.ts' --include='*.tsx' || echo "OK: no forbidden wording"
```

Hits must fail unless they are explicit negative safety copy (e.g., "No live order submission").

## Expected Safety Guarantees

- Builder does not submit live orders.
- Builder does not create executable TradeAction.
- Builder does not use live credentials in replay.
- AI remains advisory only.
- `NEXT_PUBLIC_BUILDER_API_TOKEN` must not be exposed.

## Evidence Summary Endpoint Verification

Start the backend with demo data:

```bash
export BUILDER_API_TOKEN=dev-token
export BUILDER_SEED_DEMO_STRATEGIES=1
uv run uvicorn services.api.fastapi_app:app --port 8000 &
```

### Verify each demo strategy returns correct evidence

```bash
AUTH="Authorization: Bearer dev-token"
BASE="http://localhost:8000"

# Draft strategy — all evidence missing
curl -s -H "$AUTH" "$BASE/api/strategies/demo_draft/evidence-summary" | python3 -m json.tool
# Expected: validation.status in (missing, passed), compile.status=missing, replay.status=missing, promotion.status=missing

# Validation failed — validation failed
curl -s -H "$AUTH" "$BASE/api/strategies/demo_validation_failed/evidence-summary" | python3 -m json.tool
# Expected: validation.status=failed, compile.status=missing

# Validated — validation passed, compile missing
curl -s -H "$AUTH" "$BASE/api/strategies/demo_validated/evidence-summary" | python3 -m json.tool
# Expected: validation.status=passed, compile.status=missing

# Compiled — compile hash present, replay missing
curl -s -H "$AUTH" "$BASE/api/strategies/demo_compiled/evidence-summary" | python3 -m json.tool
# Expected: compile.status=passed with hash, replay.status=missing or running

# Replay failed — replay failed with error
curl -s -H "$AUTH" "$BASE/api/strategies/demo_replay_failed/evidence-summary" | python3 -m json.tool
# Expected: replay.status=failed, compile.status=passed

# Replay passed — replay succeeded with report refs
curl -s -H "$AUTH" "$BASE/api/strategies/demo_replay_passed/evidence-summary" | python3 -m json.tool
# Expected: replay.status=passed, compile hash present, resultArtifactRefs non-empty

# Promotion requested — promotion ready
curl -s -H "$AUTH" "$BASE/api/strategies/demo_promotion_requested/evidence-summary" | python3 -m json.tool
# Expected: promotion.status=ready, replay.status=passed

# Promotion ready — all evidence present
curl -s -H "$AUTH" "$BASE/api/strategies/demo_promotion_ready/evidence-summary" | python3 -m json.tool
# Expected: promotion.status=ready, all evidence present
```

### Verify endpoint is read-only

```bash
# POST should return 404 (not a valid route)
curl -s -X POST -H "$AUTH" "$BASE/api/strategies/demo_draft/evidence-summary" | python3 -m json.tool
# Expected: 404 or method not allowed
```

### Verify no live execution fields

```bash
curl -s -H "$AUTH" "$BASE/api/strategies/demo_promotion_ready/evidence-summary" | python3 -c "
import json, sys
data = json.load(sys.stdin)
forbidden = ['submit_order', 'trade_action', 'live_credentials', 'execute_strategy', 'live_execution']
for field in forbidden:
    assert field not in str(data).lower(), f'Forbidden field found: {field}'
print('OK: no forbidden live execution fields')
"
```

## Strategy Detail UI Verification

Start both backend and frontend, then verify each strategy:

| Strategy | Lifecycle Stage | Validation | Compile | Replay | Promotion | Next Action |
|----------|----------------|------------|---------|--------|-----------|-------------|
| demo_draft | Draft | passed/missing | missing | missing | missing | Validate StrategySpec |
| demo_validation_failed | Validation failed | failed | missing | missing | missing | Fix validation errors |
| demo_validated | Validated | passed | missing | missing | missing | Compile preview artifact |
| demo_compiled | Replay missing | passed | present | missing | missing | Run replay |
| demo_replay_failed | Replay failed | passed | present | failed | missing | Review replay errors |
| demo_replay_passed | Replay passed | passed | present | passed | missing | Request promotion review |
| demo_promotion_requested | Promotion ready | passed | present | passed | ready | Inspect evidence |
| demo_promotion_ready | Promotion ready | passed | present | passed | ready | Inspect evidence |

For each strategy, verify:
1. Lifecycle panel shows the correct stage.
2. Next action card shows the correct action and explanation.
3. Evidence grid shows compile hash/ref when applicable.
4. Evidence grid shows replay job/report/artifact refs when applicable.
5. Evidence grid shows promotion request/ledger status when applicable.
6. Audit timeline shows evidence-derived events (created, validated, compiled, replay, promotion).
7. Missing evidence cards show clear "missing" state with next step guidance.
8. Builder-only safety banner is visible.

## Graceful Fallback Verification

1. Stop the backend server.
2. Open a strategy detail page in the frontend.
3. Verify:
   - Page still renders basic strategy detail (if cached).
   - A warning card appears: "Rich evidence summary unavailable."
   - No crash or unhandled error.
4. Restart the backend and verify the warning disappears on refresh.

## Demo Seed Script Verification

```bash
# Run the seed script directly
uv run python scripts/seed_demo_evidence.py
# Expected output: 8 strategies seeded, backtest jobs for applicable strategies

# Run again to verify idempotency
uv run python scripts/seed_demo_evidence.py
# Expected: same output, no duplicate records
```
