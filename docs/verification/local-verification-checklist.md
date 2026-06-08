# Local Verification Checklist

Use this checklist for local closeout verification against the Builder-owned dev
PostgreSQL database. Nautilus Builder remains Builder-only: no live order
submission, no browser-held credentials, no Nautilus-Daedalus runtime DB writes,
and manual promotion only after evidence review.

## 1. Start Builder-Owned Dev Database

```bash
docker compose -f docker-compose.dev.yml up -d postgres
```

Expected dev database credentials from `docker-compose.dev.yml` / `.env.example`:

- database: `nautilus_builder`
- user: `builder`
- password: `builder_dev`
- local endpoint: `localhost:5432`

## 2. Export Demo Environment

```bash
export BUILDER_DATABASE_URL="postgresql://builder:builder_dev@localhost:5432/nautilus_builder"
export BUILDER_API_TOKEN="replace-with-strong-demo-token"
export BUILDER_DEV_USER_ID="local_user"
export BUILDER_DEV_PROJECT_ID="local_project"
export BUILDER_DEV_ROLE="builder"
export BUILDER_ARTIFACT_ROOT="./var/builder_artifacts"
```

## 3. Apply Migrations

```bash
uv run python scripts/apply_builder_migrations.py
```

## 4. Seed Demo Data

This single command seeds demo strategies and demo evidence states into the
Builder-owned database:

```bash
uv run python scripts/seed_builder_demo_data.py
```

Expected demo states:

| Demo state | Strategy ID |
| --- | --- |
| Demo Draft Strategy | `demo_draft` |
| Demo Validation Failed Strategy | `demo_validation_failed` |
| Demo Validated Strategy | `demo_validated` |
| Demo Compiled Strategy | `demo_compiled` |
| Demo Replay Failed Strategy | `demo_replay_failed` |
| Demo Replay Passed Strategy | `demo_replay_passed` |
| Demo Promotion Requested Strategy | `demo_promotion_requested` |
| Demo Promotion Ready Strategy | `demo_promotion_ready` |

The seed command is idempotent. Run it twice to verify it does not duplicate
strategy or backtest records.

## 5. Start API

```bash
uv run uvicorn services.api.fastapi_app:create_fastapi_app \
  --factory --reload --host 0.0.0.0 --port 8000
```

## 6. Start Web

```bash
cd apps/web
npm ci
NEXT_PUBLIC_API_BASE_URL= \
BUILDER_API_BASE_URL=http://localhost:8000 \
BUILDER_API_TOKEN="$BUILDER_API_TOKEN" \
npm run dev
```

The web app should call same-origin `/api/*` paths in local mode. The Next
middleware injects the server-side `BUILDER_API_TOKEN`; do not expose Builder
API tokens through `NEXT_PUBLIC_*` variables.

## 7. Evidence Summary Smoke Test

```bash
curl -H "Authorization: Bearer replace-with-strong-demo-token" \
  http://localhost:8000/api/strategies/demo_replay_passed/evidence-summary
```

Expected:

- strategy exists
- validation state exists
- compile evidence exists when applicable
- replay evidence exists when applicable
- promotion evidence exists when applicable
- missing data is shown as missing
- unknown data is shown as unknown
- failed data is shown as failed
- passed data is shown as passed

Useful additional smoke checks:

```bash
curl -H "Authorization: Bearer replace-with-strong-demo-token" \
  http://localhost:8000/api/strategies/demo_compiled/evidence-summary
curl -H "Authorization: Bearer replace-with-strong-demo-token" \
  http://localhost:8000/api/strategies/demo_promotion_ready/evidence-summary
```

## 8. Restart Durability Test

Restart the API, then rerun the evidence-summary curl.

Expected:

- demo strategies remain
- compile evidence remains
- replay evidence remains
- promotion evidence remains
- audit timeline remains

## 9. Frontend Verification

```bash
cd apps/web
npm run typecheck
npm run build
npx vitest run --config vitest.config.mts --testTimeout=10000
```

## 10. Backend Verification

```bash
uv run ruff check .
uv run pytest
```

## 11. Safety Search

```bash
grep -R "submit_order\|Start live trading\|live trading enabled\|Auto execute\|Guaranteed profit" \
  apps/web services packages scripts docs || true
```

Review all hits. Allowed hits must be explicitly negative or safety-oriented,
for example `No live order submission`, `may_submit_order: false`, or a test
asserting forbidden wording is absent.

## Expected Safety Guarantees

- Builder-only mode remains enforced.
- Backtest and replay outputs are historical evidence-only.
- Builder does not submit live orders.
- Builder does not create executable TradeAction.
- Builder does not use live credentials in preview, replay, or backtest.
- Browser credentials remain disabled (`browser_credentials: false`).
- AI remains advisory and is not authoritative.
- Backend validation is not bypassed.
- Manual promotion happens only after review.
- The Builder database is separate from the Nautilus-Daedalus runtime database.
