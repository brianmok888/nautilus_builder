#!/usr/bin/env python3
"""Full-system verification harness for Nautilus Builder.

Usage:
    python scripts/verify_builder.py --profile local
    python scripts/verify_builder.py --profile staging
    python scripts/verify_builder.py --profile production-check

Profiles:
    local:             Runs compile, tests, forbidden-authority scan, version consistency.
    staging:           Adds Docker compose config validation.
    production-check:  Adds all production safety checks (no weak token, no wildcard CORS, etc).
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

PASS = 0
FAIL = 0


def run_check(name: str, cmd: list[str], *, cwd: Path | None = None) -> bool:
    global PASS, FAIL
    print(f"\n=== {name} ===")
    result = subprocess.run(cmd, cwd=cwd or REPO_ROOT, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"  PASSED")
        PASS += 1
        return True
    print(f"  FAILED")
    if result.stdout:
        for line in result.stdout.strip().split("\n")[-5:]:
            print(f"    {line}")
    if result.stderr:
        for line in result.stderr.strip().split("\n")[-3:]:
            print(f"    {line}")
    FAIL += 1
    return False


def run_check_shell(name: str, cmd: str, *, cwd: Path | None = None) -> bool:
    return run_check(name, ["bash", "-c", cmd], cwd=cwd)


def verify_local() -> None:
    run_check("Python compile", ["python3", "-m", "compileall", "-q", "packages", "services", "tests", "scripts"])
    run_check("Backend tests", ["python3", "-m", "pytest", "tests/", "-q", "--tb=line"])
    run_check_shell("Forbidden authority scan", "bash scripts/check_forbidden_authority.sh")
    run_check("Version consistency", ["python3", "-m", "pytest", "tests/builder_metadata", "-q", "--tb=line"])
    run_check("Hygiene tests", ["python3", "-m", "pytest", "tests/hygiene", "-q", "--tb=line"])
    run_check("Legacy removal", ["python3", "-m", "pytest", "tests/hygiene/test_legacy_removal.py", "-q", "--tb=line"])

    web_dir = REPO_ROOT / "apps" / "web"
    if web_dir.exists():
        run_check("Frontend typecheck", ["npm", "run", "typecheck"], cwd=web_dir)
        run_check("Frontend tests", ["npm", "test"], cwd=web_dir)
        run_check("Frontend build", ["npm", "run", "build"], cwd=web_dir)


def verify_staging() -> None:
    verify_local()
    run_check_shell(
        "Staging compose config",
        "docker compose -f docker-compose.staging.yml config --quiet 2>&1",
    )


def verify_production_check() -> None:
    verify_staging()

    # Production safety checks
    print("\n=== Production safety checks ===")

    # No weak token
    env_example = (REPO_ROOT / ".env.production.example").read_text()
    if "your_strong_api_token_here" in env_example.lower() or "changeme" in env_example.lower():
        print("  PASSED: Production example uses placeholder tokens")
        PASS += 1
    else:
        print("  FAILED: Production example may contain weak tokens")
        FAIL += 1

    # No NEXT_PUBLIC_BUILDER_API_TOKEN
    if "NEXT_PUBLIC_BUILDER_API_TOKEN" not in (REPO_ROOT / ".env.production.example").read_text():
        print("  PASSED: No NEXT_PUBLIC_BUILDER_API_TOKEN in production example")
        PASS += 1
    else:
        print("  FAILED: NEXT_PUBLIC_BUILDER_API_TOKEN found in production example")
        FAIL += 1

    # No wildcard CORS
    if "*" not in (REPO_ROOT / ".env.production.example").read_text().split("CORS")[1].split("\n")[0] if "CORS" in (REPO_ROOT / ".env.production.example").read_text() else "":
        print("  PASSED: No wildcard CORS in production example")
        PASS += 1
    else:
        print("  FAILED: Wildcard CORS in production example")
        FAIL += 1

    # execution_authority must be false
    run_check_shell(
        "No submit_order in production code",
        'grep -r "submit_order(" packages/ services/ --include="*.py" | grep -v test | grep -v __pycache__ | grep -v ".pyc" || true; test $(grep -r "submit_order(" packages/ services/ --include="*.py" | grep -v test | grep -v __pycache__ | grep -v ".pyc" | wc -l) -eq 0'
    )

    # No TradeAction construction
    run_check_shell(
        "No TradeAction( in production code",
        'grep -r "TradeAction(" packages/ services/ --include="*.py" | grep -v test | grep -v __pycache__ | grep -v ".pyc" || true; test $(grep -r "TradeAction(" packages/ services/ --include="*.py" | grep -v test | grep -v __pycache__ | grep -v ".pyc" | wc -l) -eq 0'
    )

    # No Daedalus imports
    run_check_shell(
        "No Daedalus imports",
        'grep -r "nautilus_daedalus\\|Nautilus.Daedalus" packages/ services/ --include="*.py" | grep -v test | grep -v __pycache__ || true; test $(grep -r "nautilus_daedalus\\|Nautilus.Daedalus" packages/ services/ --include="*.py" | grep -v test | grep -v __pycache__ | wc -l) -eq 0'
    )


PROFILES = {
    "local": verify_local,
    "staging": verify_staging,
    "production-check": verify_production_check,
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Nautilus Builder full-system verification")
    parser.add_argument("--profile", choices=list(PROFILES.keys()), default="local")
    args = parser.parse_args()

    print(f"Nautilus Builder Verification — profile: {args.profile}")
    PROFILES[args.profile]()

    print(f"\n==================================")
    print(f"Verification complete: {PASS} passed, {FAIL} failed")
    if FAIL > 0:
        sys.exit(1)
    print("All checks passed.")


if __name__ == "__main__":
    main()
