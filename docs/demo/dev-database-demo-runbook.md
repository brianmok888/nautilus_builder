# Nautilus Builder Dev Database Demo Runbook

## Purpose

Run Nautilus Builder locally with a Builder-owned PostgreSQL database and
persistent demo evidence. The Builder uses its own database (`nautilus_builder`)
and never writes to the Nautilus-Daedalus runtime database.

## Safety

This demo is **Builder-only**. It does not submit live orders, create executable
TradeAction, or use live credentials. All backtest/replay data is historical
evidence-only.

## Prerequisites

- Docker (for Postgres)
- Python 3.12+ with `uv`
- Node.js 20+ with npm

## Step 1 — Start Postgres

```bash
docker compose -f docker-compose.dev.yml up -d
```

Verify the database is healthy:

```bash
docker compose -f docker-compose.dev.yml ps
docker exec nautilus-builder-postgres pg_isready -U builder -d nautilus_builder
```

## Step 2 — Apply Migrations

```bash
export BUILDER_DATABASE_URL="postgresql://builder:builder_dev@localhost:5432/nautilus_builder"
uv run python scripts/apply_builder_migrations.py
```

This creates all Builder-owned tables under the `builder` schema.

## Step 3 — Seed Demo Data

This single command seeds both demo strategies **and** demo evidence
(backtest jobs, replay results, promotion states):

```bash
export BUILDER_DATABASE_URL="postgresql://builder:builder_dev@localhost:5432/nautilus_builder"
uv run python scripts/seed_builder_demo_data.py
```

This creates 8 demo strategies covering every lifecycle state:

1. `demo_draft` — Draft-only
2. `demo_validation_failed` — Validation failed
3. `demo_validated` — Validated, not compiled
4. `demo_compiled` — Compiled, no replay
5. `demo_replay_failed` — Replay failed
6. `demo_replay_passed` — Replay succeeded
7. `demo_promotion_requested` — Promotion requested
8. `demo_promotion_ready` — Promotion ready / approved

And seeds demo backtest evidence for strategies that have replay jobs:
- `demo_compiled` — job created (compile evidence, no replay result)
- `demo_replay_failed` — job failed
- `demo_replay_passed` — job succeeded with report artifacts
- `demo_promotion_requested` — job succeeded, promotion context
- `demo_promotion_ready` — job succeeded, approved status

The seed is **idempotent**: running it twice will not duplicate records.

## Step 4 — Start API

```bash
export BUILDER_DATABASE_URL="postgresql://builder:builder_dev@localhost:5432/nautilus_builder"
export BUILDER_ENV="local"
export BUILDER_API_TOKEN="replace-with-strong-demo-token"
export BUILDER_ARTIFACT_ROOT="./var/builder_artifacts"

uv run uvicorn services.api.fastapi_app:create_fastapi_app \
    --factory --reload --host 0.0.0.0 --port 8000
```

Verify the API is healthy:

```bash
curl http://localhost:8000/health
```

## Step 5 — Start Web

```bash
cd apps/web
npm ci
NEXT_PUBLIC_API_BASE_URL= \
BUILDER_ENV=local \
BUILDER_API_BASE_URL=http://localhost:8000 \
BUILDER_API_TOKEN="$BUILDER_API_TOKEN" \
npm run dev
```

Open: http://localhost:3000

## Step 6 — Smoke Test the Evidence Summary

```bash
curl -H "Authorization: Bearer replace-with-strong-demo-token" \
    http://localhost:8000/api/strategies/demo_compiled/evidence-summary

curl -H "Authorization: Bearer replace-with-strong-demo-token" \
    http://localhost:8000/api/strategies/demo_replay_passed/evidence-summary

curl -H "Authorization: Bearer replace-with-strong-demo-token" \
    http://localhost:8000/api/strategies/demo_promotion_ready/evidence-summary
```

Expected:
- `demo_compiled` shows compile artifact/hash
- `demo_replay_passed` shows replay job/report refs
- `demo_promotion_ready` shows promotion status

## Step 7 — Demo Walkthrough

1. Open Overview — show Builder safety status.
2. Open Strategy Specs — confirm 8 demo strategies present.
3. Open each demo strategy to view its lifecycle state.
4. Open Backtest Center — confirm top-down order:
   Strategy Selection → Selected Validated Strategy → BacktestNode Replay → Manual Promotion Review.

## Step 8 — Restart Durability Test

Restart the API process (Ctrl+C, then re-run Step 4).

After restart, re-run the smoke test from Step 6. The demo evidence should
remain visible because it is persisted in Postgres.

## Database Verification Queries

```bash
docker exec -it nautilus-builder-postgres psql -U builder -d nautilus_builder
```

```sql
-- List tables
\dt builder.*

-- Demo strategies
SELECT strategy_id, status, updated_at FROM builder.strategies ORDER BY strategy_id;

-- Demo backtest jobs
SELECT job_id, strategy_spec_version_id, stage, status FROM builder.backtest_jobs ORDER BY created_at;

-- Migrations applied
SELECT version, name, applied_at FROM builder.schema_migrations ORDER BY version;
```

## Teardown

```bash
docker compose -f docker-compose.dev.yml down -v   # -v removes the data volume
```

## Builder DB Boundary

| Database | Name | Owner | Purpose |
|----------|------|-------|---------|
| Builder | `nautilus_builder` | `builder` | Design/workflow/evidence state |
| Runtime (Daedalus) | `nautilus_daedalus_db` | `nd_runtime` | Live deterministic runtime |

The Builder never writes to the runtime DB. It may only read runtime data later
through read-only APIs, replicas, exported artifacts, dataset indices, or
promotion handoff packages.
