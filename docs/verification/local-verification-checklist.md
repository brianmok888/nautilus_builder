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

## Acceptance Smoke Test

After all checks pass, verify the UI manually:

1. Open `http://localhost:3000` — dashboard loads with safety panel.
2. Navigate to Strategy Specs — list renders with search/filter.
3. Click a strategy — detail page shows lifecycle panel, next action, evidence grid, audit timeline.
4. Navigate to Results — list renders with search/filter.
5. Open Settings — no live trading controls.

## Evidence Wiring Smoke Test

For a strategy with only a draft:
- Lifecycle should show Draft.
- Validation evidence should be missing or passed (depending on validation flags).
- Next action should be Validate StrategySpec.

For a validated strategy:
- Lifecycle should show Validated.
- Compile evidence should be missing.
- Next action should be Compile preview artifact.

For a compiled strategy (with compile hash):
- Compile artifact should show ref/hash if available.
- Replay evidence should be missing unless a replay exists.

For a replayed strategy (with backtest job):
- Replay evidence should show job/report/artifact refs if available.
- Promotion should remain missing unless requested.

For a promotion-requested strategy:
- Promotion evidence should show request id/status.

## Backend Evidence Summary Endpoint

```bash
# Verify the read-only endpoint returns existing data only
curl http://127.0.0.1:8000/api/strategies/demo_validated/evidence-summary | python3 -m json.tool
```

Expected fields: strategyId, strategyVersionId, strategyStatus, validation, compile, replay, promotion, audit.
Missing evidence must be "missing", not "passed".
