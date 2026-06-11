#!/usr/bin/env bash
# Check for secrets in .env example files and production code
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
STATUS=0

echo "=== Checking .env example files for live secrets ==="

for f in "$REPO_ROOT"/.env*.example "$REPO_ROOT"/.env.production.example; do
    [ -f "$f" ] || continue
    # Check for actual secret-like values (not placeholder text)
    if grep -qE '(api_key|secret|password|token)\s*=\s*[A-Za-z0-9]{20,}' "$f" 2>/dev/null; then
        echo "FAIL: $f contains what looks like real credentials"
        grep -nE '(api_key|secret|password|token)\s*=\s*[A-Za-z0-9]{20,}' "$f"
        STATUS=1
    fi
    # Check for forbidden NEXT_PUBLIC_BUILDER_API_TOKEN with real values
    if grep -qE 'NEXT_PUBLIC_BUILDER_API_TOKEN\s*=\s*\S+' "$f" 2>/dev/null; then
        echo "FAIL: $f contains NEXT_PUBLIC_BUILDER_API_TOKEN (browser-exposed token forbidden)"
        STATUS=1
    fi
    # Check for wildcard CORS in production
    if echo "$f" | grep -q production && grep -qE 'CORS.*\*' "$f" 2>/dev/null; then
        echo "FAIL: $f has wildcard CORS in production example"
        STATUS=1
    fi
done

# Check for hardcoded literal secret VALUES in production code (not env var name references)
# env var lookups like os.environ.get("BINANCE_API_KEY") are allowed
echo "=== Checking for hardcoded secret values in Builder production code ==="
for dir in "$REPO_ROOT/packages" "$REPO_ROOT/services"; do
    # Look for assignment of actual values to secret-named variables
    if grep -rnE '(api_key|api_secret|password|passphrase)\s*=\s*["'"'"'][A-Za-z0-9]{16,}["'"'"']' "$dir" --include='*.py' 2>/dev/null | grep -v __pycache__ | grep -v '# '; then
        echo "FAIL: Found hardcoded secret values in $dir"
        STATUS=1
    fi
done

if [ $STATUS -eq 0 ]; then
    echo "PASSED: No secret issues found"
else
    echo "FAILED: Secret issues found"
    exit 1
fi
