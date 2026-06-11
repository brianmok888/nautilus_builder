#!/usr/bin/env bash
set -euo pipefail

echo "=== Forbidden Authority Scan ==="

# Terms that grant live execution authority when present in Builder production code.
# Keep these as fixed strings: regex matching made `.submit_order` hit `may_submit_order`.
FORBIDDEN_PATTERNS=(
  # Actual API calls that submit orders
  "submit_order("
  # Actual TradeAction construction
  "TradeAction("
  # Live credential patterns
  "live_exchange_api_key"
  "live_exchange_secret"
  # Method calls that submit orders
  ".submit_order"
  # Additional credential/secret patterns from v2 spec
  "exchange_secret"
  "private_key"
  "api_secret"
)

# Scan production code by default. Docs and tests are excluded by path, not by
# allowlisting production directories after a match.
SCAN_PATHS=(
  "packages"
  "services"
  "apps/web"
  ":(exclude)apps/web/**/*.test.ts"
  ":(exclude)apps/web/**/*.test.tsx"
  ":(exclude)apps/web/**/*.spec.ts"
  ":(exclude)apps/web/**/*.spec.tsx"
  ":(exclude)apps/web/**/__tests__/**"
)

# Exact git-grep output lines that are known negative/policy literals in production
# code. Keep this list narrow; never add a directory prefix here.
# Lines are stored in a companion file for easier maintenance.
ALLOWLIST_FILE="${BASH_SOURCE[0]%/*}/authority_scan_allowlist.txt"

is_allowed_line() {
  local candidate="$1"
  if [ ! -f "$ALLOWLIST_FILE" ]; then
    return 1
  fi
  while IFS= read -r allowed_line; do
    # Skip comments and empty lines
    [[ "$allowed_line" =~ ^# ]] && continue
    [[ -z "$allowed_line" ]] && continue
    if [[ "$candidate" == *"$allowed_line"* ]]; then
      return 0
    fi
  done < "$ALLOWLIST_FILE"
  return 1
}

found_violation=false

for pattern in "${FORBIDDEN_PATTERNS[@]}"; do
  while IFS= read -r line; do
    [ -z "$line" ] && continue
    if is_allowed_line "$line"; then
      continue
    fi
    echo "FAIL: Forbidden authority pattern in production code: ${line}"
    found_violation=true
  done < <(git grep -n -F "$pattern" -- "${SCAN_PATHS[@]}" || true)
done

if $found_violation; then
  echo "=== FAILED ==="
  exit 1
fi

echo "=== PASSED ==="
echo "Production scan paths: ${SCAN_PATHS[*]}"
echo "Note: docs/tests may mention submit_order/TradeAction as negative policy examples; production code must not contain authority-granting calls."
