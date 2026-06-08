# Nautilus Builder Production Demo Runbook

## Purpose

This demo shows Nautilus Builder as a **Builder-only** strategy workflow UI. It does **not** submit live orders, create executable TradeAction, or grant live execution authority.

## Prerequisites

- Python 3.12+ with [uv](https://docs.astral.sh/uv/)
- Node.js 20+ with npm
- Docker (optional, for containerized demo)

## Quick Start: Local Backend + Frontend

### 1. Backend

```bash
# From the repo root
uv sync

# Set environment variables for demo mode
export BUILDER_ENV=local
export BUILDER_API_TOKEN=dev-token
export BUILDER_SEED_DEMO_STRATEGIES=1

# Start the API server
uv run uvicorn services.api.fastapi_app:app --reload --port 8000
```

The `BUILDER_SEED_DEMO_STRATEGIES=1` flag seeds 8 demo strategies with realistic evidence across all lifecycle states.

### 2. Frontend

```bash
# In a separate terminal
cd apps/web
npm ci

# Configure the API base URL (server-side proxy to backend)
export BUILDER_ENV=local
export NEXT_PUBLIC_API_BASE_URL=
export BUILDER_API_BASE_URL=http://127.0.0.1:8000
export BUILDER_API_TOKEN=dev-token

# Start the dev server
npm run dev
```

Open `http://localhost:3000` in your browser.

## Demo Walkthrough

### Step 1: Dashboard Overview

1. Open `http://localhost:3000`.
2. The dashboard loads with a **Builder Safety Status** panel.
3. Observe the safety banner: *"Builder-only mode. No live order submission."*

### Step 2: Strategy Specs

1. Navigate to **Strategy Specs** in the sidebar.
2. The list shows 8 demo strategies, each in a different lifecycle state.

### Step 3: Draft Strategy

1. Click on **EMA RSI Crossover — Draft**.
2. Observe:
   - Lifecycle panel shows **Draft**.
   - Validation evidence is present (passed from spec flags).
   - Compile, replay, and promotion evidence are all **missing**.
   - Next action: **Validate StrategySpec**.

### Step 4: Validation Failed Strategy

1. Click on **EMA RSI Crossover — Validation Failed**.
2. Observe:
   - Lifecycle panel shows **Validation failed**.
   - The `no_lookahead_required` flag is `false`.
   - Next action: **Fix validation errors**.
   - Blocking reason: validation failed.

### Step 5: Validated Strategy

1. Click on **EMA RSI Crossover — Validated**.
2. Observe:
   - Lifecycle panel shows **Validated**.
   - Validation evidence passed.
   - Compile artifact is **missing**.
   - Next action: **Compile preview artifact**.

### Step 6: Compiled Strategy

1. Click on **EMA RSI Crossover — Compiled**.
2. Observe:
   - Compile artifact hash shown: `sha256:demo_compile_001...`
   - Replay evidence is **missing** (job created but not yet run).
   - Next action: **Run replay**.

### Step 7: Replay Failed Strategy

1. Click on **EMA RSI Crossover — Replay Failed**.
2. Observe:
   - Lifecycle panel shows **Replay failed**.
   - Replay evidence shows the failed job reference.
   - Next action: **Review replay errors**.
   - Blocking reason: replay failed.

### Step 8: Replay Passed Strategy

1. Click on **EMA RSI Crossover — Replay Passed**.
2. Observe:
   - Lifecycle panel shows **Replay passed**.
   - Replay report/artifact refs are shown.
   - Compile hash is displayed.
   - Promotion evidence is **missing**.
   - Next action: **Request promotion review**.

### Step 9: Promotion Requested Strategy

1. Click on **EMA RSI Crossover — Promotion Requested**.
2. Observe:
   - Lifecycle panel shows **Ready for review** (approved status).
   - Replay evidence shows succeeded with report refs.
   - Promotion evidence shows **ready**.
   - Next action: **Inspect evidence**.

### Step 10: Promotion Ready Strategy

1. Click on **EMA RSI Crossover — Promotion Ready**.
2. Observe:
   - Lifecycle panel shows **Ready for review** (execution_ready status).
   - All evidence present: validation, compile, replay, promotion.
   - Audit timeline shows full lifecycle events.
   - Next action: **Inspect evidence**.

### Step 11: Execution Lane

1. Navigate to **Execution Lane** in the sidebar.
2. Observe:
   - Builder-only mode.
   - No live trading controls.
   - Paper profile section (if configured).
   - *"Builder does not submit live orders"* messaging.

### Step 12: Settings

1. Navigate to **Settings** in the sidebar.
2. Observe:
   - Model configuration for AI Builder.
   - No live trading controls.
   - No credential inputs.

## Safety Notes

Throughout the demo, the UI consistently communicates:

- **No live credentials are used.** Demo uses `dev-token` authentication only.
- **No `submit_order` path exists.** The Builder has no order submission capability.
- **No `TradeAction` is created.** Evidence is read-only aggregation.
- **AI is advisory only.** AI Builder drafts suggestions; human review is required.
- **Builder-only mode.** The safety banner and status panels reinforce this at every level.

## Docker Demo (Optional)

```bash
# From repo root
docker compose --env-file .env.example up --build
```

Set `BUILDER_SEED_DEMO_STRATEGIES=1` in your `.env` file or `docker-compose.yml`.

## API Smoke Tests

```bash
# Health check
curl -H "Authorization: Bearer dev-token" http://localhost:8000/health/backend

# List demo strategies
curl -H "Authorization: Bearer dev-token" http://localhost:8000/api/strategies

# Evidence summary for a specific strategy
curl -H "Authorization: Bearer dev-token" http://localhost:8000/api/strategies/demo_replay_passed/evidence-summary | python3 -m json.tool
```

Expected response for `demo_replay_passed`:
- `validation.status`: `"passed"`
- `compile.status`: `"passed"` with hash
- `replay.status`: `"passed"` with job refs and artifact refs
- `promotion.status`: `"missing"`
- `audit`: array with created, validated, compiled, replay events

## Restart Durability Demo

This demo proves that Builder state survives API restart when using Postgres.

### With Docker (Recommended)

```bash
# Start all services with Postgres
docker compose up -d postgres api web

# Verify demo data is seeded
curl -s -H "Authorization: Bearer $BUILDER_API_TOKEN" \
  http://localhost:8000/api/strategies/demo_replay_passed/evidence-summary | python3 -m json.tool

# Restart the API (Postgres stays up)
docker compose restart api
sleep 10

# Verify evidence still exists after restart
curl -s -H "Authorization: Bearer $BUILDER_API_TOKEN" \
  http://localhost:8000/api/strategies/demo_replay_passed/evidence-summary | python3 -m json.tool
```

The evidence summary should be identical before and after restart — strategies,
backtest jobs, compile hashes, replay reports, and promotion evidence all persist.

See [persistence-verification.md](../verification/persistence-verification.md) for the full restart durability test.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Dashboard shows "Unable to reach Nautilus Builder API" | Verify backend is running on port 8000. Check `BUILDER_API_BASE_URL`. |
| Strategy list is empty | Set `BUILDER_SEED_DEMO_STRATEGIES=1` and restart the backend. |
| Evidence summary returns 404 | Strategy ID not found. Check `/api/strategies` for valid IDs. |
| Auth errors | For this local demo, verify `BUILDER_ENV=local` and `BUILDER_API_TOKEN` match between backend and the local Next middleware process. |
| Frontend build fails | Run `cd apps/web && npm ci && npm run typecheck` for detailed errors. |
