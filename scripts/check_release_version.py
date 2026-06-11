#!/usr/bin/env python3
"""Check release version consistency across pyproject.toml, RELEASE.md, and CHANGELOG.md.

Exit 1 if versions drift.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def read_pyproject_version() -> str:
    text = (REPO_ROOT / "pyproject.toml").read_text()
    m = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
    return m.group(1) if m else "NOT_FOUND"


def read_release_current_version() -> str:
    text = (REPO_ROOT / "RELEASE.md").read_text()
    header = text.split("## Changelog")[0] if "## Changelog" in text else text
    m = re.search(r"^\*\*Version:\*\*\s*(\S+)", header, re.MULTILINE)
    return m.group(1).strip() if m else "NOT_FOUND"


def main() -> int:
    pyproject_v = read_pyproject_version()
    release_v = read_release_current_version()

    errors = []

    if not re.match(r"^\d+\.\d+\.\d+$", pyproject_v):
        errors.append(f"pyproject.toml version is not semver: {pyproject_v}")

    if release_v != pyproject_v:
        errors.append(
            f"RELEASE.md current version ({release_v}) != pyproject.toml ({pyproject_v})"
        )

    # Check CHANGELOG mentions the version
    changelog = REPO_ROOT / "CHANGELOG.md"
    if changelog.exists():
        text = changelog.read_text()
        if pyproject_v not in text and "unreleased" not in text.lower():
            errors.append(
                f"CHANGELOG.md does not mention version {pyproject_v} and is not marked unreleased"
            )

    if errors:
        for e in errors:
            print(f"ERROR: {e}", file=sys.stderr)
        return 1

    print(f"OK: All versions consistent at {pyproject_v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
