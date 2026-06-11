"""Docs source-of-truth tests — Segment 14."""
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


class TestDocsSourceTruth:
    def test_doc_directory_exists(self) -> None:
        assert (REPO_ROOT / "doc").is_dir()

    def test_docs_directory_exists(self) -> None:
        assert (REPO_ROOT / "docs").is_dir()

    def test_readme_exists(self) -> None:
        assert (REPO_ROOT / "README.md").exists()

    def test_readiness_md_exists(self) -> None:
        assert (REPO_ROOT / "READINESS.md").exists()

    def test_handguard_md_exists(self) -> None:
        assert (REPO_ROOT / "handguard.md").exists()

    def test_changelog_exists(self) -> None:
        assert (REPO_ROOT / "CHANGELOG.md").exists()

    def test_release_md_exists(self) -> None:
        assert (REPO_ROOT / "RELEASE.md").exists()

    def test_no_unreleased_claims_in_readme(self) -> None:
        """README must not claim production/live readiness."""
        content = (REPO_ROOT / "README.md").read_text().lower()
        forbidden = ["production ready", "live trading ready", "can execute live"]
        for phrase in forbidden:
            assert phrase not in content, f"README contains forbidden phrase: {phrase}"
