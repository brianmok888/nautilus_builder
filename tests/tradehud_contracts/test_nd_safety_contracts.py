"""
ND safety contract tests.

Verifies no order authority, no browser credentials, no browser Redis/PostgreSQL.
These tests scan all source files for forbidden patterns.
"""
import re
from pathlib import Path

import pytest

# Directories to scan
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

SCAN_DIRS = [
    PROJECT_ROOT / "packages" / "tradehud_contracts",
    PROJECT_ROOT / "services" / "api" / "routes",
    PROJECT_ROOT / "scripts" / "tradehud_seed_redis.py",
    PROJECT_ROOT / "scripts" / "tradehud_replay_nd_fixtures.py",
]

# Forbidden executable patterns (in code, not comments/docs)
FORBIDDEN_CODE_PATTERNS = [
    (r"submit_order\s*\(", "submit_order() call"),
    (r"createTradeAction\s*\(", "createTradeAction() call"),
    (r"create_trade_action\s*\(", "create_trade_action() call"),
    (r"force_approve\s*\(", "force_approve() call"),
    (r"forceApprove\s*\(", "forceApprove() call"),
]

# Forbidden in browser-facing files only
FORBIDDEN_BROWSER_PATTERNS = [
    r"NEXT_PUBLIC_REDIS_URL",
    r"NEXT_PUBLIC_DATABASE_URL",
    r"NEXT_PUBLIC_EXCHANGE_SECRET",
]


def collect_python_files() -> list[Path]:
    files = []
    for target in SCAN_DIRS:
        if target.is_file() and target.suffix == ".py":
            files.append(target)
        elif target.is_dir():
            files.extend(target.rglob("*.py"))
    return files


def strip_comments_and_strings(content: str) -> str:
    """Remove comments, docstrings, and string literals for code-only scan."""
    # Remove triple-quoted strings
    content = re.sub(r'""".*?"""', '', content, flags=re.DOTALL)
    content = re.sub(r"'''.*?'''", '', content, flags=re.DOTALL)
    # Remove single-line comments
    content = re.sub(r'#.*$', '', content, flags=re.MULTILINE)
    # Remove string literals
    content = re.sub(r'"[^"]*"', '""', content)
    content = re.sub(r"'[^']*'", '""', content)
    return content


class TestNoOrderAuthority:
    """No executable order authority in any TradeHUD backend file."""

    @pytest.mark.parametrize("pattern,label", FORBIDDEN_CODE_PATTERNS)
    def test_no_submit_order_calls(self, pattern, label):
        violations = []
        for f in collect_python_files():
            if not f.exists():
                continue
            raw = f.read_text()
            code = strip_comments_and_strings(raw)
            if re.search(pattern, code, re.IGNORECASE):
                violations.append(str(f))
        assert violations == [], f"{label} found in: {violations}"


class TestNoBrowserCredentials:
    """No NEXT_PUBLIC credential variables in browser files."""

    def test_no_browser_redis_url(self):
        web_dir = PROJECT_ROOT / "apps" / "web"
        if not web_dir.exists():
            pytest.skip("apps/web not found")
        violations = []
        for f in web_dir.rglob("*.ts*"):
            if ".test." in f.name or "node_modules" in str(f):
                continue
            content = f.read_text(errors="ignore")
            for pattern in FORBIDDEN_BROWSER_PATTERNS:
                # Allow in test files that check for absence
                if ".test." in f.name:
                    continue
                if re.search(pattern, content):
                    violations.append(f"{f}: {pattern}")
        assert violations == [], f"Browser credential patterns found: {violations}"


class TestAdapterReadOnly:
    """Redis adapter must only use read commands."""

    def test_adapter_has_no_write_commands(self):
        adapter_path = PROJECT_ROOT / "packages" / "tradehud_contracts" / "redis_adapter.py"
        if not adapter_path.exists():
            pytest.skip("redis_adapter.py not found")
        code = strip_comments_and_strings(adapter_path.read_text())
        forbidden_cmds = ["xadd", "xdel", "xtrim", "publish(", "flushdb", "flushall", ".set("]
        for cmd in forbidden_cmds:
            assert cmd not in code.lower(), f"Forbidden Redis command in adapter: {cmd}"


class TestSafetyBoundary:
    """TradeHUD must remain observational."""

    def test_no_browser_to_redis_direct(self):
        web_dir = PROJECT_ROOT / "apps" / "web"
        if not web_dir.exists():
            pytest.skip("apps/web not found")
        for f in web_dir.rglob("*.ts*"):
            if "node_modules" in str(f) or ".test." in f.name:
                continue
            content = f.read_text(errors="ignore")
            code = re.sub(r'//.*$', '', content, flags=re.MULTILINE)
            code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
            assert "new Redis(" not in code, f"Browser Redis client in {f}"
            assert "new Pool(" not in code, f"Browser PostgreSQL in {f}"

    def test_replay_script_is_local_only(self):
        script = PROJECT_ROOT / "scripts" / "tradehud_replay_nd_fixtures.py"
        if not script.exists():
            pytest.skip("replay script not found")
        content = script.read_text()
        assert "LOCAL DEVELOPMENT ONLY" in content, "Replay script must declare LOCAL ONLY"
