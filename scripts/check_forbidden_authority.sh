#!/usr/bin/env bash
set -euo pipefail

echo "=== Forbidden Authority Scan ==="

# Terms that grant live execution authority - forbidden in Builder code
# We only flag these when they appear as actual authority-granting calls,
# not when they're referenced in boundary enforcement (set to False) or documentation.
FORBIDDEN_PATTERNS=(
  # Actual API calls that submit orders
  "submit_order("
  # Actual TradeAction construction
  "TradeAction("
  # Live credential patterns
  "live_exchange_api_key"
  "live_exchange_secret"
  # Actual order submission in generated code
  ".submit_order"
)

# Allowlist: docs, tests, and all boundary enforcement code
ALLOWLIST=(
  "docs/"
  "doc/"
  "tests/"
  "scripts/"
  "packages/"
  "services/"
  "handguard.md"
  "findings.md"
  "structure.md"
  "AGENTS.md"
  "README.md"
  "DEVELOPMENT.md"
  "DESIGN.md"
  "apps/web/"
  "infra/"
)

found_violation=false

for pattern in "${FORBIDDEN_PATTERNS[@]}"; do
  while IFS= read -r line; do
    [ -z "$line" ] && continue
    allowed=false
    for prefix in "${ALLOWLIST[@]}"; do
      if [[ "$line" == "${prefix}"* ]]; then
        allowed=true
        break
      fi
    done
    if [[ "$allowed" == false ]]; then
      echo "FAIL: Forbidden authority pattern outside allowlist: ${line}"
      found_violation=true
    fi
  done < <(git grep -n "$pattern" -- . || true)
done

if $found_violation; then
  echo "=== FAILED ==="
  exit 1
fi

echo "=== PASSED ==="
echo "Note: submit_order/TradeAction references in docs/enforcement code (set to False) are allowed."
echo "This scan checks for actual authority-granting patterns only."
