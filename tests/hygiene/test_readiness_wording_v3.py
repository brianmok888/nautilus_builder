"""Readiness wording hygiene test (Segment 17). Scans docs for unsafe live-readiness phrases."""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

UNSAFE_PHRASES = [
    "production ready",
    "live ready",
    "auto execute",
    "auto-trade",
    "guaranteed profit",
    "approved for live",
    "live trading enabled",
]

ALLOWED_CONTEXTS = [
    "not production ready",
    "not live ready",
    "out of scope",
    "not owned",
    "forbidden",
    "must not",
    "does not",
    "builder-only",
    "builder only",
    "signal-preview",
    "shadow/paper",
    "advisory only",
    "no live",
    "no order",
    "grep -r",   # grep commands scanning for forbidden phrases
    "grep -R",   # grep commands scanning for forbidden phrases
]

DOC_EXTENSIONS = {".md", ".rst", ".txt"}


def _scan_docs() -> list[tuple[Path, int, str, str]]:
    findings: list[tuple[Path, int, str, str]] = []
    docs_dir = REPO_ROOT / "docs"
    if not docs_dir.exists():
        return findings
    for doc_file in sorted(docs_dir.rglob("*")):
        if doc_file.suffix not in DOC_EXTENSIONS:
            continue
        if doc_file.name.startswith(".") or "node_modules" in str(doc_file):
            continue
        content = doc_file.read_text(errors="replace")
        for i, line in enumerate(content.split("\n"), 1):
            lower = line.lower()
            for phrase in UNSAFE_PHRASES:
                if phrase in lower:
                    # Check if it's in an allowed negative context
                    if any(ctx in lower for ctx in ALLOWED_CONTEXTS):
                        continue
                    # Check for "is not" / "does not" negation
                    if "not " + phrase in lower or "does not " in lower:
                        continue
                    # Skip lines that are grep commands scanning for forbidden patterns
                    if "grep" in lower and ("submit_order" in lower or "forbidden" in lower):
                        continue
                    findings.append((doc_file.relative_to(REPO_ROOT), i, phrase, line.strip()))
    return findings


class TestReadinessWording:
    def test_no_unsafe_live_readiness_claims_in_docs(self) -> None:
        findings = _scan_docs()
        if findings:
            lines = [f"  {path}:{line} — '{phrase}' in: {text}" for path, line, phrase, text in findings]
            raise AssertionError("Unsafe readiness phrases found in docs:\n" + "\n".join(lines))

    def test_readiness_matrix_exists(self) -> None:
        assert (REPO_ROOT / "docs" / "readiness" / "readiness-matrix.md").exists()

    def test_deprecation_inventory_exists(self) -> None:
        assert (REPO_ROOT / "docs" / "deprecations" / "deprecation-inventory.md").exists()

    def test_compatibility_doc_exists(self) -> None:
        assert (REPO_ROOT / "docs" / "compatibility" / "daedalus-nt-compatibility.md").exists()
