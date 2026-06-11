"""Tests for repo hygiene: no committed generated artifacts."""
from __future__ import annotations

import subprocess
import os

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _git_tracked_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "--cached"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip().splitlines()


def test_no_committed_node_modules():
    tracked = _git_tracked_files()
    violations = [f for f in tracked if f.startswith("node_modules/")]
    assert violations == [], f"Committed node_modules files: {violations[:5]}"


def test_no_committed_pycache():
    tracked = _git_tracked_files()
    violations = [f for f in tracked if "/__pycache__/" in f]
    assert violations == [], f"Committed __pycache__ files: {violations[:5]}"


def test_no_committed_pytest_cache():
    tracked = _git_tracked_files()
    violations = [f for f in tracked if f.startswith(".pytest_cache/")]
    assert violations == [], f"Committed .pytest_cache files: {violations[:5]}"


def test_no_committed_vite_vitest_cache():
    tracked = _git_tracked_files()
    violations = [f for f in tracked if ".vite/" in f or ".vitest/" in f]
    assert violations == [], f"Committed .vite/.vitest files: {violations[:5]}"


def test_no_committed_next_cache():
    tracked = _git_tracked_files()
    violations = [f for f in tracked if ".next/cache" in f]
    assert violations == [], f"Committed .next/cache files: {violations[:5]}"


def test_hygiene_script_exists_and_executable():
    script_path = os.path.join(REPO_ROOT, "scripts", "check_repo_hygiene.sh")
    assert os.path.isfile(script_path), f"Hygiene script missing: {script_path}"
    assert os.access(script_path, os.X_OK), f"Hygiene script not executable: {script_path}"


def test_forbidden_authority_script_exists_and_executable():
    script_path = os.path.join(REPO_ROOT, "scripts", "check_forbidden_authority.sh")
    assert os.path.isfile(script_path), f"Authority scan script missing: {script_path}"
    assert os.access(script_path, os.X_OK), f"Authority scan script not executable: {script_path}"


def test_forbidden_authority_script_scans_production_dirs_by_default():
    script_path = os.path.join(REPO_ROOT, "scripts", "check_forbidden_authority.sh")
    with open(script_path) as f:
        content = f.read()

    assert "SCAN_PATHS=(" in content
    assert '"packages"' in content
    assert '"services"' in content
    assert '"apps/web"' in content
    assert '"packages/"' not in content
    assert '"services/"' not in content
    assert '"apps/web/"' not in content
    assert "git grep -n -F" in content


def test_hygiene_script_passes():
    result = subprocess.run(
        ["bash", "scripts/check_repo_hygiene.sh"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Hygiene script failed:\n{result.stdout}\n{result.stderr}"


def test_forbidden_authority_script_passes():
    result = subprocess.run(
        ["bash", "scripts/check_forbidden_authority.sh"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Authority scan failed:\n{result.stdout}\n{result.stderr}"


def test_gitignore_covers_required_entries():
    gitignore_path = os.path.join(REPO_ROOT, ".gitignore")
    with open(gitignore_path) as f:
        content = f.read()
    required = ["__pycache__/", "node_modules/", ".pytest_cache/", ".vite/", ".vitest/", ".ruff_cache/", ".mypy_cache/", ".venv/", ".next/"]
    missing = [entry for entry in required if entry not in content]
    assert missing == [], f".gitignore missing entries: {missing}"


def test_forbidden_authority_script_checks_expanded_patterns():
    """v2: scan must include exchange_secret, private_key, api_secret."""
    script_path = os.path.join(REPO_ROOT, "scripts", "check_forbidden_authority.sh")
    with open(script_path) as f:
        content = f.read()
    assert '"exchange_secret"' in content
    assert '"private_key"' in content
    assert '"api_secret"' in content


def test_verify_all_script_exists():
    script_path = os.path.join(REPO_ROOT, "scripts", "verify_all.sh")
    assert os.path.isfile(script_path), f"verify_all.sh missing: {script_path}"
    assert os.access(script_path, os.X_OK), f"verify_all.sh not executable"


def test_authority_allowlist_file_exists():
    allowlist_path = os.path.join(REPO_ROOT, "scripts", "authority_scan_allowlist.txt")
    assert os.path.isfile(allowlist_path), f"allowlist file missing: {allowlist_path}"
