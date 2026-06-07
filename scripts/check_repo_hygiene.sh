#!/usr/bin/env bash
# Repo hygiene check: fails if generated/cache artifacts are tracked by git.
set -euo pipefail

forbidden=(
  node_modules
  .vite
  .vitest
  .next
  dist
  build
  .pytest_cache
  .ruff_cache
  .mypy_cache
  htmlcov
  test-results
  playwright-report
)

failed=0
for path in "${forbidden[@]}"; do
  if git ls-files | grep -qE "(^|/)$path(/|$)"; then
    echo "ERROR: Forbidden generated/cache artifact is tracked: $path"
    git ls-files | grep -E "(^|/)$path(/|$)" || true
    failed=1
  fi
done

if [ "$failed" -eq 0 ]; then
  echo "Repo hygiene: OK (no forbidden tracked artifacts)"
fi
exit "$failed"
