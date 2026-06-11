#!/usr/bin/env bash
# Production smoke test — verifies deployment from docs alone
# Segment R v4
set -euo pipefail

BASE_URL="${1:-http://localhost:8000}"
TOKEN="${2:-}"
STATUS=0

echo "=== Production Smoke Test ==="
echo "Base URL: $BASE_URL"

# Health endpoints
echo "--- Health endpoints ---"
for endpoint in /health/live /health/ready /health/build /health/policy; do
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL$endpoint" 2>/dev/null || echo "000")
    if [ "$HTTP_CODE" = "200" ]; then
        echo "  PASS: $endpoint -> $HTTP_CODE"
    else
        echo "  FAIL: $endpoint -> $HTTP_CODE"
        STATUS=1
    fi
done

# Auth-protected endpoints
if [ -n "$TOKEN" ]; then
    echo "--- Auth-protected endpoints ---"
    for endpoint in /api/strategies /api/readiness /api/adapters; do
        HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer $TOKEN" "$BASE_URL$endpoint" 2>/dev/null || echo "000")
        if [ "$HTTP_CODE" = "200" ]; then
            echo "  PASS: $endpoint -> $HTTP_CODE"
        else
            echo "  FAIL: $endpoint -> $HTTP_CODE"
            STATUS=1
        fi
    done

    # Verify unauthenticated access is rejected
    echo "--- Unauthenticated access rejection ---"
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/strategies" 2>/dev/null || echo "000")
    if [ "$HTTP_CODE" = "401" ]; then
        echo "  PASS: unauthenticated /api/strategies -> $HTTP_CODE"
    else
        echo "  FAIL: unauthenticated /api/strategies -> $HTTP_CODE (expected 401)"
        STATUS=1
    fi
fi

echo "--- Forbidden authority check ---"
# Verify Builder doesn't expose order submission
if curl -s "$BASE_URL" 2>/dev/null | grep -qi "submit_order\|TradeAction"; then
    echo "  FAIL: Found forbidden authority in API response"
    STATUS=1
else
    echo "  PASS: No forbidden authority in API response"
fi

if [ $STATUS -eq 0 ]; then
    echo "=== SMOKE PASSED ==="
else
    echo "=== SMOKE FAILED ==="
    exit 1
fi
