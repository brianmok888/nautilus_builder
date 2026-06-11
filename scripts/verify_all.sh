#!/usr/bin/env bash
# verify_all.sh — Local verification parity with CI.
# Runs the same checks as .github/workflows/ci.yml where practical.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

PASS=0
FAIL=0

run_check() {
    local name="$1"
    shift
    echo ""
    echo "=== $name ==="
    if "$@"; then
        echo "  PASSED"
        ((PASS++))
    else
        echo "  FAILED"
        ((FAIL++))
    fi
}

# Backend compile
run_check "Python compile" python3 -m compileall -q packages services tests scripts

# Backend tests
run_check "Backend tests" python3 -m pytest tests/ -q --tb=line

# Forbidden authority scan
run_check "Forbidden authority scan" bash scripts/check_forbidden_authority.sh

# Hygiene tests
run_check "Hygiene tests" python3 -m pytest tests/hygiene -q --tb=line

# Version consistency
run_check "Version consistency" python3 -m pytest tests/builder_metadata -q --tb=line

# Frontend typecheck
if [ -d "apps/web" ]; then
    run_check "Frontend typecheck" bash -c 'cd apps/web && npm run typecheck'
    run_check "Frontend tests" bash -c 'cd apps/web && npm test'
    run_check "Frontend build" bash -c 'cd apps/web && npm run build'
fi

echo ""
echo "=================================="
echo "Verification complete: $PASS passed, $FAIL failed"
if [ "$FAIL" -gt 0 ]; then
    exit 1
fi
echo "All checks passed."
