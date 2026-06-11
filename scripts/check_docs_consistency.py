#!/usr/bin/env python3
"""Check docs consistency — verify docs reflect implementation truth."""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def check_readme_no_live_trading_claim() -> list[str]:
    """README must not claim live trading readiness."""
    issues = []
    readme = REPO_ROOT / "README.md"
    if not readme.exists():
        return ["README.md not found"]

    text = readme.read_text().lower()
    forbidden_claims = [
        "live trading ready",
        "production trading ready",
        "safe to trade live",
        "live execution ready",
    ]
    for claim in forbidden_claims:
        if claim in text:
            issues.append(f"README contains forbidden claim: '{claim}'")

    return issues


def check_readiness_md_exists() -> list[str]:
    """READINESS.md must exist and match readiness service."""
    issues = []
    path = REPO_ROOT / "READINESS.md"
    if not path.exists():
        issues.append("READINESS.md not found")
        return issues

    text = path.read_text()
    if "out of scope" not in text.lower():
        issues.append("READINESS.md does not mention 'out of scope' for live execution")
    if "live" not in text.lower():
        issues.append("READINESS.md does not mention 'live' at all")

    return issues


def check_version_consistency() -> list[str]:
    """Version strings in docs should be consistent."""
    issues = []
    pyproject = REPO_ROOT / "pyproject.toml"
    if not pyproject.exists():
        return ["pyproject.toml not found"]

    text = pyproject.read_text()
    m = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
    if not m:
        issues.append("No version found in pyproject.toml")
        return issues

    version = m.group(1)

    # Check RELEASE.md
    release = REPO_ROOT / "RELEASE.md"
    if release.exists():
        release_text = release.read_text()
        if version not in release_text and "unreleased" not in release_text.lower():
            issues.append(f"RELEASE.md does not mention version {version}")

    return issues


def check_builder_boundary_in_docs() -> list[str]:
    """Docs must mention Builder-only boundary."""
    issues = []
    doc_files = list((REPO_ROOT / "doc").glob("*.md")) + list((REPO_ROOT / "docs").glob("**/*.md"))

    builder_boundary_found = False
    for doc in doc_files:
        text = doc.read_text().lower()
        if "builder" in text and ("boundary" in text or "builder-only" in text or "does not" in text):
            builder_boundary_found = True
            break

    if not builder_boundary_found:
        issues.append("No doc file mentions Builder-only boundary")

    return issues


def main() -> int:
    all_issues: list[str] = []

    all_issues.extend(check_readme_no_live_trading_claim())
    all_issues.extend(check_readiness_md_exists())
    all_issues.extend(check_version_consistency())
    all_issues.extend(check_builder_boundary_in_docs())

    if all_issues:
        print("Docs consistency check FAILED:")
        for issue in all_issues:
            print(f"  - {issue}")
        return 1

    print("Docs consistency check PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
