#!/usr/bin/env python3
"""Check release version consistency across pyproject.toml, RELEASE.md, and CHANGELOG.md.

Exit 1 if versions drift or if the first concrete changelog version exceeds pyproject
unless the section is explicitly named "Unreleased".
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


def parse_first_concrete_changelog_version(changelog_text: str) -> tuple[str | None, str | None]:
    """Return (section_header, version) for the first concrete version section.

    Returns (None, None) if only Unreleased is present.
    """
    for line in changelog_text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("## "):
            continue
        header = stripped[3:].strip()
        # Skip Unreleased section
        if header.lower().startswith("unreleased"):
            continue
        # Extract version from header like "v0.5.0 - 2026-06-11" or "v0.5.0"
        m = re.match(r"v?(\d+\.\d+\.\d+)", header)
        if m:
            return header, m.group(1)
    return None, None


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

    # Check CHANGELOG structure and version alignment
    changelog = REPO_ROOT / "CHANGELOG.md"
    if changelog.exists():
        text = changelog.read_text()

        # The first concrete version in changelog must match pyproject
        header, changelog_v = parse_first_concrete_changelog_version(text)
        if changelog_v is not None and changelog_v != pyproject_v:
            errors.append(
                f"CHANGELOG.md first concrete version ({changelog_v} from '{header}') "
                f"!= pyproject.toml ({pyproject_v}). "
                f"If unreleased work exists, use '## Unreleased' header."
            )

        # pyproject version must appear somewhere in changelog
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
