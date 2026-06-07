#!/usr/bin/env bash
set -euo pipefail

echo "=== Repo Hygiene Check ==="

FORBIDDEN=(
  "node_modules"
  ".vite"
  ".vitest"
  ".next/cache"
  "__pycache__"
  ".pytest_cache"
  ".ruff_cache"
  ".mypy_cache"
  ".venv"
)

found_violation=false

for path in "${FORBIDDEN[@]}"; do
  if git ls-files --cached | grep -qE "(^|/)${path}(/|$)"; then
    echo "FAIL: Forbidden committed artifact: ${path}"
    found_violation=true
  fi
done

if $found_violation; then
  echo "=== FAILED ==="
  exit 1
fi

echo "=== PASSED ==="
