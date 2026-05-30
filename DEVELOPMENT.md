# Nautilus Builder — Development Guide

## Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.12+ | Backend runtime |
| Node.js | 18+ | Frontend build |
| Docker + Compose | Latest | Full-stack local dev |
| uv (optional) | Latest | Python dependency management |
| Git | Latest | Version control |

## Quick Start (5 commands)

```bash
git clone <repo-url> nautilus_builder && cd nautilus_builder
cp .env.example .env                    # Configure environment
docker compose up -d                    # Start full stack
# API: http://localhost:8000  |  Web: http://localhost:3000
docker compose exec api curl -s http://localhost:8000/health
```

## Local Development (without Docker)

### Backend only

```bash
# Using uv (recommended)
uv sync
uv run uvicorn 'services.api.fastapi_app:create_fastapi_app' --factory --host 127.0.0.1 --port 8000

# Or using plain Python
pip install -e ".[test]"
python3 -m services.api.dev_server --host 127.0.0.1 --port 8000
```

### Frontend only

```bash
cd apps/web
npm install
npm run dev
# Opens on http://localhost:3000
```

### Full stack with scripts

```bash
# Start both API + frontend
./scripts/run_dev.sh

# Start API only
./scripts/run_dev.sh --api-only

# Start frontend only
./scripts/run_dev.sh --web-only
```

## Testing

### Quick test run

```bash
./scripts/run_tests.sh            # Python tests only (fast)
```

### Full verification gate

```bash
./scripts/run_tests.sh --full     # Python + frontend + build
```

### Targeted tests by domain

```bash
pytest tests/strategy_spec/       # Strategy spec schema
pytest tests/strategy_validation/ # Validation rules
pytest tests/strategy_compiler/   # Compilation
pytest tests/backtest_runner/     # Backtest pipeline
pytest tests/execution_lane/      # Execution lane contracts
pytest tests/workflow_spine/      # Workflow persistence
pytest tests/ai_builder/          # AI advisory drafting
```

### Frontend tests

```bash
cd apps/web
npx vitest run                    # Unit tests
npx tsc --noEmit                  # TypeScript check
npm run build                     # Production build
```

### E2E tests (Playwright)

```bash
cd apps/web
npx playwright install chromium
npm run test:e2e
```

## Project Structure

```
nautilus_builder/
├── packages/              # Python domain layer (113 files)
│   ├── strategy_spec/     # StrategySpec Pydantic schema
│   ├── strategy_validation/  # Hard-rule checks
│   ├── strategy_compiler/    # Compile artifacts
│   ├── ai_builder/        # Advisory AI drafting
│   ├── backtest_runner/   # Backtest pipeline
│   ├── execution_lane/    # TradingNode runtime plans
│   ├── adapter_registry/  # Adapter profiles
│   ├── instrument_registry/  # Instrument definitions
│   └── ...                # 20+ more domain packages
├── services/api/          # FastAPI routes (thin over packages/*)
├── services/workers/      # Backend worker entrypoints
├── apps/web/              # Next.js 15 + Ant Design 6
├── tests/                 # 470+ pytest tests
├── doc/                   # Source-truth specs and hardguards
├── scripts/               # Operational scripts
├── docker-compose.yml     # Full-stack Docker
└── pyproject.toml         # Python package manifest
```

## Architecture Boundaries

### What Builder owns
- Strategy authoring, validation, compilation
- Backtest configuration and result normalization
- Promotion contracts and evidence tracking
- Advisory AI drafting (output is always draft-stage)

### What Builder does NOT own
- Live order execution (`submit_order`, `TradeAction` — Daedalus owns these)
- Exchange credentials at runtime (worker-only)
- Direct TradingNode control from API routes
- Telegram/aiogram-dialog integrations (Daedalus owns these)

### Hard rules (see handguard.md)
- `execution_authority` must remain `False` in all Builder code paths
- Browser UI must never collect exchange credentials
- No `eval()`, `exec()`, `subprocess`, `socket` in strategy code
- Adapter resolution through registry, not hardcoded

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `BUILDER_API_TOKEN` | `change-me-in-production` | API authentication token |
| `APP_ENV` | (unset) | Set to `production` for safety checks |
| `POSTGRES_PASSWORD` | `builder_dev` | PostgreSQL password |
| `BUILDER_DATABASE_URL` | (auto) | PostgreSQL connection URL |
| `BUILDER_CORS_ORIGINS` | (unset) | Comma-separated CORS origins |
| `BUILDER_SEED_DEMO_STRATEGIES` | `1` | Seed demo data on startup |
| `BUILDER_ALLOW_FIXTURE_FALLBACK` | (unset) | Enable fixture fallback (dev only) |
| `BUILDER_RATE_LIMIT` | (unset) | Requests per minute per IP |
| `OPENAI_API_KEY` | (unset) | AI provider key (optional) |
| `OPENAI_BASE_URL` | (unset) | AI provider endpoint (optional) |
| `OPENAI_MODEL` | (unset) | AI provider model (optional) |

Full reference: `.env.example`

## Troubleshooting

### "ModuleNotFoundError: No module named 'packages'"
Ensure you're running from the repo root, or install in development mode:
```bash
pip install -e ".[test]"
```

### "Port 8000 already in use"
Another process is using the port. Find and stop it:
```bash
lsof -i :8000
kill <PID>
```

### "Docker compose fails to start"
- Ensure Docker daemon is running: `docker info`
- Check for stale containers: `docker compose down -v`
- Verify `.env` exists: `cp .env.example .env`

### "Frontend build fails"
- Clear node_modules: `cd apps/web && rm -rf node_modules && npm install`
- Check Node.js version: `node --version` (needs 18+)

### "Tests fail after pulling changes"
- Reinstall dependencies: `uv sync` or `pip install -e ".[test]"`
- Clear pytest cache: `pytest --cache-clear`

### "Database connection refused"
- Start Postgres: `docker compose up -d postgres`
- Check health: `docker compose exec postgres pg_isready`

## Verification Checklist

Before submitting changes, verify:

```bash
python3 -m compileall -q packages services tests  # No compile errors
python3 -m pytest tests/ -q --tb=line             # All tests pass
cd apps/web && npx tsc --noEmit                    # TypeScript clean
cd apps/web && npx vitest run                      # Frontend tests pass
cd apps/web && npm run build                       # Build succeeds
```

## References

- `doc/nautilus_builder_spec.md` — Product specification
- `doc/nautilus_builder_hardguards.md` — Runtime safety boundaries
- `DESIGN.md` — UI design source of truth
- `structure.md` — Repository structure review
- `findings.md` — Review findings and status
- `handguard.md` — Enforced boundary constraints
