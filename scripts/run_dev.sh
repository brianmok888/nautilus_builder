#!/usr/bin/env bash
# run_dev.sh — Start Nautilus Builder development environment
# Usage: ./scripts/run_dev.sh [--api-only|--web-only|--full]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT_DIR"

MODE="${1:-full}"

usage() {
    echo "Usage: $0 [--api-only|--web-only|--full|--help]"
    echo ""
    echo "  --api-only   Start only the FastAPI backend on :8000"
    echo "  --web-only   Start only the Next.js frontend on :3000"
    echo "  --full       Start both API and frontend (default)"
    echo "  --help       Show this help"
    exit 0
}

case "$MODE" in
    --help|-h) usage ;;
    --api-only) MODE="api" ;;
    --web-only) MODE="web" ;;
    --full)     MODE="full" ;;
    *)          echo "Unknown option: $MODE"; usage ;;
esac

# Load .env if present
if [ -f .env ]; then
    set -a; source .env; set +a
fi

# Check for .env.example → .env if no .env exists
if [ ! -f .env ] && [ -f .env.example ]; then
    echo "ℹ  No .env found. Copy .env.example to .env and customize:"
    echo "   cp .env.example .env"
fi

cleanup() {
    if [ -n "${API_PID:-}" ]; then kill "$API_PID" 2>/dev/null || true; fi
    if [ -n "${WEB_PID:-}" ]; then kill "$WEB_PID" 2>/dev/null || true; fi
    echo ""
    echo "🛑 Dev servers stopped."
}
trap cleanup EXIT INT TERM

start_api() {
    echo "🚀 Starting API server on http://localhost:8000 ..."
    if command -v uv &>/dev/null; then
        uv run uvicorn 'services.api.fastapi_app:create_fastapi_app' \
            --factory --host 127.0.0.1 --port 8000 &
        API_PID=$!
    else
        python3 -m services.api.dev_server --host 127.0.0.1 --port 8000 &
        API_PID=$!
    fi
}

start_web() {
    echo "🎨 Starting Next.js frontend on http://localhost:3000 ..."
    cd "$ROOT_DIR/apps/web"
    if [ ! -d node_modules ]; then
        echo "📦 Installing frontend dependencies ..."
        npm install --frozen-lockfile 2>/dev/null || npm install
    fi
    npm run dev &
    WEB_PID=$!
    cd "$ROOT_DIR"
}

echo "🔧 Nautilus Builder — Development Mode ($MODE)"
echo "─────────────────────────────────────────────"

case "$MODE" in
    api)
        start_api
        ;;
    web)
        start_web
        ;;
    full)
        start_api
        sleep 2
        start_web
        ;;
esac

echo ""
echo "✅ Development servers running. Press Ctrl+C to stop."
echo "   API:  http://localhost:8000"
echo "   Docs: http://localhost:8000/docs"
if [ "$MODE" != "api" ]; then
    echo "   Web:  http://localhost:3000"
fi
echo ""

wait
