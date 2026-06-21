#!/usr/bin/env bash
# scripts/e2e_webui.sh — Nautilus Builder e2e web UI test via agent-browser.
#
# DEFAULT tool for web UI e2e testing in this repo. Uses agent-browser
# (npm i -g agent-browser) to drive a real headless Chrome against the
# running stack (frontend on :3000 + backend on :8000).
#
# Prereqs:
#   - agent-browser installed globally:  npm i -g agent-browser
#   - Stack running (see scripts/run_dev.sh), e.g.:
#       BUILDER_ENV=local APP_ENV=local \
#       BUILDER_API_TOKEN=<token> \
#       uv run uvicorn 'services.api.fastapi_app:create_fastapi_app' --factory --port 8000 &
#       cd apps/web && BUILDER_API_TOKEN=<token> npm run dev &
#
# Usage:
#   bash scripts/e2e_webui.sh                       # http://127.0.0.1:3000
#   E2E_BASE=http://127.0.0.1:3000 bash scripts/e2e_webui.sh
#   E2E_SHOTS=/tmp/shots bash scripts/e2e_webui.sh
#
# Exit code = number of failures (0 = all green). Prints a PASS/FAIL summary.
set -uo pipefail
BASE="${E2E_BASE:-http://127.0.0.1:3000}"
SHOT_DIR="${E2E_SHOTS:-/tmp/e2e_shots}"
mkdir -p "$SHOT_DIR"

# Locate agent-browser (user prefix or PATH).
AGENT_BROWSER="$(command -v agent-browser || true)"
if [ -z "$AGENT_BROWSER" ] && [ -x "$HOME/.npm-global/bin/agent-browser" ]; then
  AGENT_BROWSER="$HOME/.npm-global/bin/agent-browser"
fi
if [ -z "$AGENT_BROWSER" ]; then
  echo "FAIL: agent-browser not found. Install with: npm i -g agent-browser" >&2
  exit 99
fi
export PATH="$(dirname "$AGENT_BROWSER"):$PATH"

PASS=0; FAIL=0; FAILED_ITEMS=""
fail(){ echo "FAIL: $1"; FAIL=$((FAIL+1)); FAILED_ITEMS="${FAILED_ITEMS}|$1"; }
pass(){ echo "PASS: $1"; PASS=$((PASS+1)); }

echo "== e2e_webui.sh | base=$BASE | shots=$SHOT_DIR =="

# 1) Stack reachability checks (fail fast with a clear message if the stack is down).
api_code="$(curl -s -m 6 -o /dev/null -w '%{http_code}' "$BASE/health/backend" 2>/dev/null || echo 000)"
if [ "$api_code" = "200" ]; then pass "backend reachable via frontend proxy (/health/backend 200)"; else fail "backend not reachable via $BASE/health/backend (got $api_code) — start stack with scripts/run_dev.sh"; fi

# 2) Home loads.
agent-browser close --all >/dev/null 2>&1
agent-browser open "$BASE" >/dev/null 2>&1
agent-browser wait 2000 >/dev/null 2>&1
TITLE="$(agent-browser get title 2>/dev/null | head -1)"
if echo "$TITLE" | grep -q "Nautilus Builder"; then pass "home loads (title ok)"; else fail "home title wrong: '$TITLE'"; fi
agent-browser screenshot "$SHOT_DIR/01_home.png" >/dev/null 2>&1

# 3) Route smoke: every main route renders nav + exposes NO order-submission UI.
for r in /builder /backtests /execution /strategies /pipeline /results /config; do
  agent-browser open "$BASE$r" >/dev/null 2>&1
  agent-browser wait 1500 >/dev/null 2>&1
  SNAP="$(agent-browser snapshot -i 2>/dev/null)"
  if echo "$SNAP" | grep -q 'navigation "Nautilus Builder navigation"'; then
    if echo "$SNAP" | grep -iqE 'submit.{0,3}order|place.{0,3}order'; then
      fail "$r renders but exposes order-submission UI (SAFETY CONTRACT BREAK)"
    else
      pass "$r renders nav + no order-submission UI"
    fi
  else
    fail "$r did not render nav (404/error?)"
  fi
  agent-browser screenshot "$SHOT_DIR/$(echo "$r" | tr / _)_route.png" >/dev/null 2>&1
done

# 4) Execution Lane safety contract: all live controls disabled, no order authority.
agent-browser open "$BASE/execution" >/dev/null 2>&1
agent-browser wait 2000 >/dev/null 2>&1
EXEC="$(agent-browser snapshot 2>/dev/null)"
echo "$EXEC" | grep -iqE 'may[_ ]submit[_ ]order.{0,4}:?.{0,3}false' && pass "execution lane may_submit_order=false" || fail "execution lane may_submit_order not false"
echo "$EXEC" | grep -iqE 'credential[_ ]inputs[_ ]allowed.{0,4}:?.{0,3}false' && pass "execution lane credential_inputs_allowed=false" || fail "execution lane credential_inputs_allowed not false"
echo "$EXEC" | grep -qi 'Browser runtime actions are disabled' && pass "execution lane actions disabled text present" || fail "execution lane disabled text missing"

# 5) Frontend<->Backend wired: no "request failed" alert on execution lane.
if echo "$EXEC" | grep -q 'Execution lane request failed'; then
  fail "execution lane API request failed (frontend-backend proxy broken)"
else
  pass "execution lane API request succeeded (frontend-backend proxy wired)"
fi

# 6) Client-side routing works (click a nav link, expect URL change).
agent-browser open "$BASE" >/dev/null 2>&1
agent-browser wait 1500 >/dev/null 2>&1
HOME_SNAP="$(agent-browser snapshot -i 2>/dev/null)"
RESULTS_REF="$(echo "$HOME_SNAP" | grep -oE 'link "bar-chart Results" \[ref=e[0-9]+\]' | grep -oE 'e[0-9]+' | head -1)"
if [ -n "$RESULTS_REF" ]; then
  agent-browser click "@$RESULTS_REF" >/dev/null 2>&1
  agent-browser wait 2000 >/dev/null 2>&1
  CUR_URL="$(agent-browser get url 2>/dev/null | head -1)"
  if echo "$CUR_URL" | grep -q '/results'; then pass "client-side nav click routes to /results"; else fail "client-side nav click did not route (url=$CUR_URL)"; fi
else
  fail "Results nav link ref not found in home snapshot"
fi
agent-browser screenshot "$SHOT_DIR/$(echo '/results' | tr / _)_client_nav.png" >/dev/null 2>&1

agent-browser close --all >/dev/null 2>&1

echo ""
echo "==================== E2E SUMMARY ===================="
echo "PASS=$PASS FAIL=$FAIL"
if [ "$FAIL" -eq 0 ]; then
  echo "RESULT: ALL GREEN"
else
  echo "RESULT: FAILURES:${FAILED_ITEMS}"
fi
echo "Screenshots: $SHOT_DIR"
exit "$FAIL"
