# Nautilus Builder E2E deployment instructions

**Last updated:** 2026-05-27  
**Target:** single private VM / staging host running Builder API, Builder web UI, and optional local infra.  
**Authority boundary:** this deploy runs Strategy Builder, Backtest Center, and gated Execution Lane contracts. It must not grant browser live-order authority.

## 0. Reference contract

- NautilusTrader install/support source: <https://nautilustrader.io/docs/latest/getting_started/installation/>
- NautilusTrader upstream repo: <https://github.com/nautechsystems/nautilus_trader>
- Builder pin: `nautilus_trader==1.227.0` from `pyproject.toml`
- Builder web ports: API `8000`, Next.js web `3000`
- Optional local infra: Postgres `5432`, Redis `6379`, MinIO `9000/9001`

The current official NautilusTrader install docs say supported Python versions are 3.12-3.14 on supported 64-bit platforms and recommend `uv` with CPython. Builder currently requires Python `>=3.12` and installs the pinned NT version through `uv sync`.

## 1. VM prerequisites

Ubuntu 22.04+ x86_64 is the safest target because NautilusTrader binary wheels are CI-tested on Ubuntu 22.04-compatible glibc.

```bash
sudo apt-get update
sudo apt-get install -y \
  ca-certificates curl git build-essential pkg-config \
  python3 python3-venv python3-dev \
  nodejs npm postgresql-client \
  redis-tools jq lsof

# Recommended: install current uv if not present.
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
uv --version
uv python install 3.12

# Recommended Node path if distro node is old: install Node 22 with your standard node manager.
node --version
npm --version
```

Expected:

- Python 3.12 installed/available through `uv`.
- Node 22.x preferred for parity with CI/dev; Node 20+ may work but should not be the acceptance baseline.
- Network access to PyPI and the NautilusTrader package index/PyPI wheel source.

## 2. Clone or update the repo

```bash
mkdir -p ~/projects
cd ~/projects

if [ ! -d nautilus_builder/.git ]; then
  git clone https://github.com/brianmok888/nautilus_builder.git
fi

cd ~/projects/nautilus_builder
git fetch origin
git checkout master
git pull --ff-only origin master
```

For redeploys, stop old services before rebuilding to avoid stale Next chunk mismatches:

```bash
sudo systemctl stop nautilus-builder-web 2>/dev/null || true
sudo systemctl stop nautilus-builder-api 2>/dev/null || true
pkill -f 'next (start|dev).*3000' 2>/dev/null || true
pkill -f 'uvicorn.*services.api.fastapi_app' 2>/dev/null || true
rm -rf apps/web/.next
```

## 3. Python + NautilusTrader dependencies

Install Builder and test extras. This installs the pinned NautilusTrader runtime (`nautilus_trader==1.227.0`) plus FastAPI, Redis, Psycopg, Uvicorn, Pydantic, pytest, and PyYAML.

```bash
cd ~/projects/nautilus_builder
uv python pin 3.12 || true
uv sync --extra test
```

Verify NautilusTrader is installed and matches the Builder pin:

```bash
uv run python - <<'PY'
import importlib.metadata
from packages.backtest_runner.runtime_check import assert_nautilus_runtime_version
status = assert_nautilus_runtime_version()
print(status.message)
print('import version:', importlib.metadata.version('nautilus_trader'))
PY
```

Run the minimal real NT engine smoke:

```bash
uv run python - <<'PY'
from packages.backtest_runner.real_engine_smoke import run_real_nautilus_backtest_smoke
print(run_real_nautilus_backtest_smoke())
PY
```

Run catalog-backed NT replay smoke tests:

```bash
uv run pytest \
  tests/backtest_runner/test_runtime_dependency_check.py \
  tests/backtest_runner/test_real_nautilus_engine_smoke.py \
  tests/backtest_runner/test_catalog_backed_nautilus_replay_smoke.py \
  tests/backtest_runner/test_strategy_spec_catalog_replay.py \
  -q
```

## 4. Optional local infra

For local/staging persistence experiments, start the supplied Postgres, Redis, and MinIO stack:

```bash
cd ~/projects/nautilus_builder
# Depending on your Docker install, use either docker compose or docker-compose.
docker compose -f infra/docker-compose.yml up -d

docker compose -f infra/docker-compose.yml ps
```

Optional environment values:

```bash
export BUILDER_DATABASE_URL='postgresql://builder:builder_local_only@127.0.0.1:5432/nautilus_builder'
export BUILDER_REDIS_URL='redis://127.0.0.1:6379/0'
```

Apply SQL migrations only when using the local Postgres schema explicitly:

```bash
for f in infra/migrations/*.sql; do
  psql "$BUILDER_DATABASE_URL" -v ON_ERROR_STOP=1 -f "$f"
done
```

## 5. Runtime environment files

Create a private API environment file:

```bash
sudo mkdir -p /etc/nautilus-builder
sudo tee /etc/nautilus-builder/api.env >/dev/null <<'EOF_API'
BUILDER_ENV=staging
BUILDER_API_TOKEN=replace-with-long-random-dev-token
BUILDER_DEV_USER_ID=vm_operator
BUILDER_DEV_PROJECT_ID=project_alpha
BUILDER_DEV_ROLE=builder
BUILDER_AI_AUDIT_SQLITE_PATH=/home/mok/projects/nautilus_builder/.local/ai_audit.sqlite3

# Optional AI provider. Leave unset to keep the offline advisory fixture path.
# OPENAI_API_KEY=sk-...
# OPENAI_BASE_URL=https://api.openai.com/v1
# OPENAI_MODEL=gpt-4.1-mini
# OPENAI_TIMEOUT_SECS=30

# Optional native TradingNode runner. Default is contract/simulated session safety mode.
# BUILDER_EXECUTION_LANE_TRADINGNODE_RUNNER=native
EOF_API
sudo chmod 600 /etc/nautilus-builder/api.env
```

Create a web environment file:

```bash
sudo tee /etc/nautilus-builder/web.env >/dev/null <<'EOF_WEB'
BUILDER_ENV=staging
BUILDER_API_BASE_URL=http://127.0.0.1:8000
NEXT_PUBLIC_API_BASE_URL=
EOF_WEB
sudo chmod 600 /etc/nautilus-builder/web.env
```

The Next middleware only injects `BUILDER_API_TOKEN` when `BUILDER_ENV=local`.
In staging, keep raw Builder API tokens out of the web process and browser
bundle; authenticated API verification should use server-side curl commands or
an explicit upstream auth/reverse-proxy layer. Do **not** set
`NEXT_PUBLIC_BUILDER_API_TOKEN`; raw Builder API tokens must not be exposed to
browser bundles.

Credential slots for execution lanes are stored by the backend in `.env.execution.local` only after an operator explicitly saves venue-prefixed paper/sandbox credentials from the UI or API. This file must remain gitignored and server-side:

```bash
cd ~/projects/nautilus_builder
touch .env.execution.local
chmod 600 .env.execution.local
```

## 6. Build the web UI

```bash
cd ~/projects/nautilus_builder/apps/web
npm ci
npx playwright install --with-deps chromium
npm run typecheck
rm -rf .next
npm run build
npx vitest run --config vitest.config.mts --testTimeout=10000
```

The build should show `ƒ Middleware` in the route summary. That middleware sends no-store headers for app HTML so stale VM pages do not reference removed `_next/static` chunks after redeploys.

## 7. Full local verification before starting services

```bash
cd ~/projects/nautilus_builder
uv run python -m compileall -q packages services tests
uv run pytest \
  tests/strategy_spec tests/strategy_validation tests/adapter_registry \
  tests/instrument_registry tests/strategy_compiler tests/backtest_jobs \
  tests/runtime_events tests/backtest_runner tests/catalog_datasets \
  tests/research_jobs tests/execution_lane tests/lifecycle \
  tests/strategy_registry tests/promotions tests/web tests/ai_builder \
  tests/integration tests/workflow_spine tests/auth tests/api tests/infrastructure \
  -q

cd apps/web
npm run typecheck
rm -rf .next
npm run build
npx vitest run --config vitest.config.mts --testTimeout=10000
npm run test:e2e
```

If VM resources are limited, run the focused deployment gate first:

```bash
cd ~/projects/nautilus_builder
uv run python -m services.backend_runtime --require-nautilus
uv run pytest tests/backtest_runner tests/execution_lane tests/api tests/integration -q
cd apps/web && npm run typecheck && rm -rf .next && npm run build && npx vitest run --config vitest.config.mts --testTimeout=10000
```

## 8. Start services manually for smoke testing

Terminal 1 — API:

```bash
cd ~/projects/nautilus_builder
set -a
. /etc/nautilus-builder/api.env
set +a
uv run uvicorn 'services.api.fastapi_app:create_fastapi_app' --factory --host 0.0.0.0 --port 8000
```

Terminal 2 — Web:

```bash
cd ~/projects/nautilus_builder/apps/web
set -a
. /etc/nautilus-builder/web.env
set +a
npm run start -- --hostname 0.0.0.0 --port 3000
```

Smoke:

```bash
curl -fsS http://127.0.0.1:8000/health | jq .
curl -fsS http://127.0.0.1:3000/ >/tmp/nb-home.html

# Confirm app HTML no-store headers and static assets load.
curl -I http://127.0.0.1:3000/
asset=$(grep -oE '/_next/static/[^" ]+\.(css|js)' /tmp/nb-home.html | head -1)
curl -I "http://127.0.0.1:3000${asset}"
```

Expected:

- `/health` returns JSON.
- `curl -I /` includes `cache-control: no-store, max-age=0, must-revalidate`.
- Static asset request returns `200 OK`, not `400`/`404`.

## 9. Install systemd services

API unit:

```bash
sudo tee /etc/systemd/system/nautilus-builder-api.service >/dev/null <<'EOF_SERVICE'
[Unit]
Description=Nautilus Builder FastAPI
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=mok
WorkingDirectory=/home/mok/projects/nautilus_builder
EnvironmentFile=/etc/nautilus-builder/api.env
ExecStart=/home/mok/.local/bin/uv run uvicorn 'services.api.fastapi_app:create_fastapi_app' --factory --host 0.0.0.0 --port 8000
Restart=on-failure
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF_SERVICE
```

Web unit:

```bash
sudo tee /etc/systemd/system/nautilus-builder-web.service >/dev/null <<'EOF_SERVICE'
[Unit]
Description=Nautilus Builder Next.js Web
After=network-online.target nautilus-builder-api.service
Wants=network-online.target

[Service]
Type=simple
User=mok
WorkingDirectory=/home/mok/projects/nautilus_builder/apps/web
EnvironmentFile=/etc/nautilus-builder/web.env
ExecStart=/usr/bin/npm run start -- --hostname 0.0.0.0 --port 3000
Restart=on-failure
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF_SERVICE
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable nautilus-builder-api nautilus-builder-web
sudo systemctl restart nautilus-builder-api
sudo systemctl restart nautilus-builder-web
sudo systemctl status nautilus-builder-api --no-pager
sudo systemctl status nautilus-builder-web --no-pager
```

## 10. Browser/E2E smoke from the VM or an operator workstation

```bash
HOST=192.168.4.82
curl -fsS "http://${HOST}:8000/health" | jq .
curl -fsS "http://${HOST}:3000/" >/tmp/nb-remote-home.html
asset=$(grep -oE '/_next/static/[^" ]+\.(css|js)' /tmp/nb-remote-home.html | head -1)
curl -I "http://${HOST}:3000${asset}"
```

Run a Playwright console/error smoke against the deployed web server:

```bash
cd ~/projects/nautilus_builder/apps/web
node - <<'NODE'
const { chromium } = require('@playwright/test');
const host = process.env.NB_HOST || 'http://192.168.4.82:3000';
(async () => {
  const browser = await chromium.launch({ headless: true });
  for (const path of ['/', '/config', '/backtests/bt_job_001', '/results/res_001']) {
    const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
    const logs = [];
    page.on('console', msg => logs.push(`${msg.type()}: ${msg.text()}`));
    page.on('pageerror', e => logs.push(`pageerror: ${e.message}`));
    page.on('requestfailed', req => logs.push(`requestfailed: ${req.url()} ${req.failure()?.errorText}`));
    await page.goto(`${host}${path}`, { waitUntil: 'networkidle', timeout: 30000 });
    const body = await page.locator('body').innerText();
    console.log(path, body.slice(0, 120).replace(/\n/g, ' | '));
    if (body.includes('Application error')) throw new Error(`Application error on ${path}`);
    const bad = logs.filter(line => /ChunkLoadError|_next\/static.*(400|404)|pageerror/.test(line));
    if (bad.length) throw new Error(`${path} browser errors:\n${bad.join('\n')}`);
    await page.close();
  }
  await browser.close();
})();
NODE
```

## 11. Functional E2E acceptance path

Use a private VM browser at `http://<host>:3000`:

1. **Strategy Builder**
   - Enter a natural-language strategy prompt.
   - Generate/apply StrategySpec draft.
   - Confirm validation errors are visible if the prompt/spec violates guardrails.
   - Confirm no credential or live-order fields appear.
2. **Backtest Center**
   - Select strategy/version, adapter, instrument, data type, timeframe, and date range.
   - Create a backtest job.
   - Run BacktestNode.
   - Confirm job events and artifact refs appear.
3. **Manual promotion**
   - Request shadow/signal-preview promotion only after backtest evidence.
   - Confirm `may_submit_order: false` remains visible.
4. **Execution Lane**
   - Save paper/sandbox credential slot only if needed; confirm UI returns only redacted keys/slot ref.
   - Wire paper profile.
   - Queue paper command and run backend worker/session.
   - Confirm lifecycle events/reports return to UI.
   - Stop/dispose the session.

Do not perform live execution from this E2E script. Live TradingNode operation requires a separate production approval/runbook with real auth, real risk gates, reconciliation, manual approval, and non-public credential handling.

## 12. Troubleshooting

### Application error / pure text UI / chunk load errors

Symptoms:

- Browser shows `Application error: a client-side exception has occurred`.
- UI appears as pure unstyled text.
- Console shows `ChunkLoadError` or `_next/static/*.js` / `*.css` returning `400` or `404`.

Recovery:

```bash
cd ~/projects/nautilus_builder
sudo systemctl stop nautilus-builder-web
rm -rf apps/web/.next
cd apps/web
npm ci
npm run build
sudo systemctl restart nautilus-builder-web

curl -fsS http://127.0.0.1:3000/ >/tmp/nb-home.html
asset=$(grep -oE '/_next/static/[^" ]+\.(css|js)' /tmp/nb-home.html | head -1)
curl -I "http://127.0.0.1:3000${asset}"
```

### API unreachable

```bash
sudo systemctl status nautilus-builder-api --no-pager
journalctl -u nautilus-builder-api -n 200 --no-pager
curl -v http://127.0.0.1:8000/health
```

Check:

- `uv sync --extra test` completed.
- `nautilus_trader==1.227.0` imports.
- API curl checks use the private `/etc/nautilus-builder/api.env` `BUILDER_API_TOKEN`; do not pass that token to the staging web process and do not set `BUILDER_DEV_AUTH_TOKEN` outside local development.
- Firewall allows port `8000` only if you intentionally expose API; otherwise keep API local and web proxy-facing.

### Missing PyYAML during tests

Use the test extra:

```bash
cd ~/projects/nautilus_builder
uv sync --extra test
uv run python -c 'import yaml; print(yaml.__version__)'
```

### NautilusTrader install mismatch

```bash
uv run python -m packages.backtest_runner.runtime_check
uv pip show nautilus_trader
```

If mismatch persists, recreate the venv:

```bash
rm -rf .venv
uv sync --extra test
```

## 13. Redeploy checklist

```bash
cd ~/projects/nautilus_builder
git fetch origin && git checkout master && git pull --ff-only origin master
sudo systemctl stop nautilus-builder-web nautilus-builder-api
rm -rf apps/web/.next
uv sync --extra test
uv run python -m services.backend_runtime --require-nautilus
cd apps/web && npm ci && npm run typecheck && rm -rf .next && npm run build && npx vitest run --config vitest.config.mts --testTimeout=10000
cd ~/projects/nautilus_builder
sudo systemctl restart nautilus-builder-api
sudo systemctl restart nautilus-builder-web
curl -fsS http://127.0.0.1:8000/health | jq .
curl -I http://127.0.0.1:3000/
```

Stop condition: API health returns JSON, web HTML has no-store headers, first `_next/static` asset returns `200`, Playwright smoke has no `Application error` or `ChunkLoadError`, and Strategy Builder / Backtest Center / Execution Lane remain separated with no browser live-order authority.
