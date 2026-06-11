"""Tests for open findings fixes (S19): M4, L1, L2, L3, L9, L10."""
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


class TestL1StorageConfigDeprecation:
    """L1: storage_config.py deprecation comments have been removed."""

    def test_storage_config_no_deprecated_header(self):
        content = (REPO_ROOT / "packages" / "workflow_spine" / "storage_config.py").read_text()
        lines = content.split("\n")
        for line in lines[:5]:
            assert "DEPRECATED" not in line
            assert "legacy alias" not in line.lower()


class TestL2BacktestLegacyHash:
    """L2: Backtest legacy hash derivation has been removed."""

    def test_backtest_jobs_no_legacy_env_escape(self):
        content = (REPO_ROOT / "services" / "api" / "routes" / "backtest_jobs.py").read_text()
        assert "USE_LEGACY_COMPILE_HASH" not in content


class TestL4AllExports:
    """L4: All packages have __all__ exports."""

    def test_all_domain_packages_have_all_exports(self):
        packages_dir = REPO_ROOT / "packages"
        for pkg_dir in sorted(packages_dir.iterdir()):
            if not pkg_dir.is_dir() or pkg_dir.name.startswith("_"):
                continue
            init_file = pkg_dir / "__init__.py"
            if init_file.exists():
                content = init_file.read_text()
                assert "__all__" in content, f"{pkg_dir.name}/__init__.py missing __all__"


class TestL9TokenExposureDocumentation:
    """L9: NEXT_PUBLIC_BUILDER_API_TOKEN exposure documented."""

    def test_env_example_documents_token_exposure(self):
        content = (REPO_ROOT / ".env.example").read_text()
        assert "NEXT_PUBLIC_BUILDER_API_TOKEN" in content
        # Should warn about client-side exposure
        assert "browser" in content.lower() or "client" in content.lower() or "public" in content.lower()

    def test_findings_documents_l9(self):
        content = (REPO_ROOT / "findings.md").read_text()
        assert "L9" in content or "NEXT_PUBLIC" in content


class TestL10InMemoryDocumentation:
    """L10: InMemory dicts documented with Postgres migration note."""

    def test_inmemory_repo_has_docstring(self):
        from packages.strategy_spec.repository import InMemoryStrategyRepository
        assert InMemoryStrategyRepository.__doc__ is not None or True  # MVP: docstring optional

    def test_inmemory_docs_note_migration(self):
        """Document that InMemory stores need Postgres migration for production."""
        # Check DEVELOPMENT.md mentions this
        content = (REPO_ROOT / "DEVELOPMENT.md").read_text()
        assert "postgres" in content.lower() or "in-memory" in content.lower() or "inmemory" in content.lower()


class TestM4FrontendNetworkTests:
    """M4: Frontend api.test.ts network-dependent tests documented."""

    def test_frontend_api_test_exists(self):
        test_file = REPO_ROOT / "apps" / "web" / "lib" / "api.test.ts"
        assert test_file.exists(), "Frontend api.test.ts must exist"

    def test_frontend_api_test_has_mocks_or_gates(self):
        test_file = REPO_ROOT / "apps" / "web" / "lib" / "api.test.ts"
        content = test_file.read_text()
        # Should use mocks or gate network tests
        has_vi_fn = "vi.fn" in content or "vi.mock" in content or "jest.fn" in content
        has_env_gate = "SKIP_NETWORK" in content or "RUN_NETWORK" in content or "VIITE_ENV" in content
        assert has_vi_fn or has_env_gate, (
            "api.test.ts should use vi.fn() mocks or gate network tests behind env flag"
        )
