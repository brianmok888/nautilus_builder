"""Tests for the verify_builder.py script (Segment 18)."""
from __future__ import annotations

import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT = REPO_ROOT / "scripts" / "verify_builder.py"


class TestVerifyBuilderScript:
    def test_script_exists_and_executable(self) -> None:
        assert SCRIPT.exists()

    def test_script_has_all_profiles(self) -> None:
        content = SCRIPT.read_text()
        for profile in ("local", "staging", "production-check"):
            assert profile in content, f"Missing profile: {profile}"

    def test_script_includes_required_checks(self) -> None:
        content = SCRIPT.read_text()
        assert "compileall" in content
        assert "pytest" in content
        assert "check_forbidden_authority" in content
        assert "typecheck" in content

    def test_script_help_flag_works(self) -> None:
        result = subprocess.run(
            ["python3", str(SCRIPT), "--help"],
            capture_output=True, text=True, timeout=10, cwd=REPO_ROOT,
        )
        assert result.returncode == 0
        assert "profile" in result.stdout.lower()
