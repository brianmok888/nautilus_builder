"""Readiness wording guard tests — Segment 3.

Ensures no production-facing docs make unsafe live-readiness claims
unless explicitly negated, and that READINESS.md exists with a proper matrix.
"""
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

# Wording patterns that indicate unsafe live-readiness claims
UNSAFE_PATTERNS = [
    r"production\s+ready",
    r"live\s+ready",
    r"live\s+trading\s+ready",
    r"can\s+execute\s+live\s+orders",
    r"Builder\s+submits\s+orders",
    r"Builder\s+creates\s+TradeAction",
]

# Allowed context patterns that negate the unsafe claim
ALLOWED_NEGATIONS = [
    r"not\s+production\s+ready",
    r"not\s+live.trading\s+ready",
    r"out\s+of\s+scope",
    r"forbidden",
    r"Daedalus.owned",
    r"requires\s+external\s+evidence",
    r"not\s+claimed",
    r"not\s+live.ready",
]

# Directories to scan for wording violations
SCAN_DIRS = ["doc", "docs", "README.md", "structure.md", "handguard.md", "READINESS.md"]


def _collect_doc_files() -> list[Path]:
    files: list[Path] = []
    for entry in SCAN_DIRS:
        p = REPO_ROOT / entry
        if p.is_file():
            files.append(p)
        elif p.is_dir():
            files.extend(p.rglob("*.md"))
    return sorted(files)


def _has_negation_in_context(line: str, match_start: int, match_end: int) -> bool:
    context = line[max(0, match_start - 80):match_end + 80].lower()
    for neg in ALLOWED_NEGATIONS:
        if re.search(neg, context, re.IGNORECASE):
            return True
    return False


class TestReadinessWording:
    def test_readiness_md_exists(self) -> None:
        assert (REPO_ROOT / "READINESS.md").exists(), "READINESS.md missing"

    def test_readiness_md_has_matrix(self) -> None:
        content = (REPO_ROOT / "READINESS.md").read_text()
        assert "Strategy authoring" in content or "strategy authoring" in content
        assert "Live execution" in content or "live execution" in content
        assert "out of scope" in content.lower() or "forbidden" in content.lower()

    @pytest.mark.parametrize("doc_file", _collect_doc_files(), ids=lambda p: str(p.relative_to(REPO_ROOT)))
    def test_no_unsafe_live_readiness_claims(self, doc_file: Path) -> None:
        content = doc_file.read_text(encoding="utf-8", errors="replace")
        lines = content.split("\n")
        in_code_fence = False

        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("```"):
                in_code_fence = not in_code_fence
                continue
            if in_code_fence:
                continue
            if stripped.startswith("//") or stripped.startswith("#!"):
                continue

            for pattern in UNSAFE_PATTERNS:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    if not _has_negation_in_context(line, match.start(), match.end()):
                        pytest.fail(
                            f"Unsafe readiness claim in {doc_file.relative_to(REPO_ROOT)}:{i+1}: "
                            f"{stripped[:120]}"
                        )
