#!/usr/bin/env bash
# run_tests.sh — Run full Nautilus Builder verification suite
# Usage: ./scripts/run_tests.sh [--quick|--full|--frontend]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT_DIR"

MODE="${1:-quick}"
EXTRA_ARGS=()

case "$MODE" in
    --quick)    MODE="quick" ;;
    --full)     MODE="full" ;;
    --frontend) MODE="frontend" ;;
    --help|-h)
        echo "Usage: $0 [--quick|--full|--frontend|--help]"
        echo ""
        echo "  --quick     Python tests only (default)"
        echo "  --full      Python + frontend + build checks"
        echo "  --frontend  Frontend tests only"
        exit 0
        ;;
    *)  echo "Unknown: $MODE"; exit 1 ;;
esac

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

pass=0
fail=0

run_step() {
    local name="$1"
    shift
    echo ""
    echo -e "${YELLOW}▶ $name${NC}"
    if "$@"; then
        echo -e "${GREEN}✓ $name passed${NC}"
        ((pass++))
    else
        echo -e "${RED}✗ $name FAILED${NC}"
        ((fail++))
    fi
}

echo "🧪 Nautilus Builder — Test Suite ($MODE)"
echo "══════════════════════════════════════════"

# ── Python compile check ──
run_step "Python compilation" python3 -m compileall -q packages services tests

# ── Python tests ──
run_step "Python pytest" python3 -m pytest tests/ -q --tb=short

if [ "$MODE" = "quick" ]; then
    echo ""
    echo "══════════════════════════════════════════"
    echo -e "${GREEN}Passed: $pass${NC}  ${RED}Failed: $fail${NC}"
    exit $((fail > 0 ? 1 : 0))
fi

# ── Frontend checks (full mode) ──
if [ "$MODE" = "full" ]; then
    if [ -d apps/web ]; then
        cd apps/web
        run_step "TypeScript check" npx tsc --noEmit
        run_step "Frontend unit tests" npx vitest run
        run_step "Frontend build" npm run build
        cd "$ROOT_DIR"
    else
        echo "⚠  No apps/web directory, skipping frontend tests"
    fi
fi

# ── Frontend-only mode ──
if [ "$MODE" = "frontend" ]; then
    if [ -d apps/web ]; then
        cd apps/web
        run_step "TypeScript check" npx tsc --noEmit
        run_step "Frontend unit tests" npx vitest run
        cd "$ROOT_DIR"
    fi
fi

echo ""
echo "══════════════════════════════════════════"
echo -e "${GREEN}Passed: $pass${NC}  ${RED}Failed: $fail${NC}"

exit $((fail > 0 ? 1 : 0))
